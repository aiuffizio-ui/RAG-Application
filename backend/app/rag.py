import os
import asyncio
from typing import List, Tuple

from fastapi import FastAPI, Request, Header, HTTPException
import gitlab
from openai import OpenAI

# -------------------- CONFIG --------------------

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITLAB_URL = os.getenv("GITLAB_URL")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
MAX_TOKENS = 1200
MAX_DIFF_CHARS = 12000
CHUNK_SIZE = 4000

AI_NOTE_MARKER = "<!-- AI_CODE_REVIEW -->"

# -------------------- APP INIT --------------------

app = FastAPI()
client = OpenAI(api_key=OPENAI_API_KEY)
gl = gitlab.Gitlab(GITLAB_URL, private_token=GITLAB_TOKEN)

_semaphore = asyncio.Semaphore(3)

# -------------------- TOKEN TRACKER --------------------

class TokenTracker:
    def __init__(self):
        self.total = 0

    def add(self, n: int):
        self.total += n

tracker = TokenTracker()

# -------------------- HELPERS --------------------

def _verify_secret(token: str) -> bool:
    return token == WEBHOOK_SECRET


def _chunk_diff_text(text: str) -> List[str]:
    chunks = []
    while text:
        chunks.append(text[:CHUNK_SIZE])
        text = text[CHUNK_SIZE:]
    return chunks


def _assemble_full_diff(changes: list) -> Tuple[str, int]:
    buf = []
    skipped = 0
    for c in changes:
        diff = c.get("diff", "")
        if not diff:
            skipped += 1
            continue
        buf.append(f"\n# File: {c.get('new_path')}\n{diff}")
        if sum(len(x) for x in buf) > MAX_DIFF_CHARS:
            break
    return "\n".join(buf), skipped


def _build_prompt(
    repo: str,
    title: str,
    author: str,
    diff: str,
) -> str:
    return f"""
You are performing a security-focused enterprise code review.

Repository: {repo}
Merge Request: {title}
Author: {author}

Review ONLY the following diff.

Output format:
EXECUTIVE DECISION:
- APPROVE / REQUEST CHANGES / NEEDS HUMAN REVIEW

CRITICAL:
- <file> — <issue> — <fix>

HIGH:
- ...

(omit empty sections)

Diff:
{diff}
"""


def _build_merge_prompt(reviews: List[str]) -> str:
    return f"""
Merge the following reviews.

Rules:
- Use ONLY listed issues
- Remove duplicates
- Omit empty severities
- If CRITICAL exists, prepend EXACT line:
MANDATORY_APPROVAL_REQUIRED

Partial reviews:
{chr(10).join(reviews)}
"""

# -------------------- OPENAI --------------------

async def _call_openai(prompt: str, max_tokens: int) -> str:
    async with _semaphore:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a conservative enterprise code auditor."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=max_tokens,
        )

        content = resp.choices[0].message.content or ""

        if resp.usage and resp.usage.total_tokens:
            tracker.add(resp.usage.total_tokens)

        return content.strip()


def _sanitize_reviews(reviews: List[str]) -> List[str]:
    clean = []
    for r in reviews:
        if not r:
            continue
        if "<file" in r or "<line" in r:
            continue
        clean.append(r)
    return clean


def _has_critical(review: str) -> bool:
    lines = review.splitlines()
    in_critical = False

    for l in lines:
        if l.strip() == "CRITICAL:":
            in_critical = True
            continue
        if in_critical:
            if l.strip().endswith(":"):
                return False
            if l.strip().startswith("-"):
                return True
    return False

# -------------------- WEBHOOK --------------------

@app.post("/webhook")
async def webhook(request: Request, x_gitlab_token: str = Header(default="")):
    if not _verify_secret(x_gitlab_token):
        raise HTTPException(status_code=403)

    payload = await request.json()
    if payload.get("object_kind") != "merge_request":
        return {"ok": True}

    mr_attr = payload["object_attributes"]
    project_id = int(payload["project"]["id"])
    mr_iid = int(mr_attr["iid"])

    project = gl.projects.get(project_id)
    mr = project.mergerequests.get(mr_iid)
    changes = mr.changes()["changes"]

    full_diff, skipped = _assemble_full_diff(changes)
    if not full_diff.strip():
        return {"ok": True, "skipped": True}

    chunks = _chunk_diff_text(full_diff)

    reviews = []
    for c in chunks:
        prompt = _build_prompt(
            payload["project"]["path_with_namespace"],
            mr_attr.get("title", ""),
            mr_attr.get("author", {}).get("name", ""),
            c,
        )
        reviews.append(await _call_openai(prompt, MAX_TOKENS))

    reviews = _sanitize_reviews(reviews)
    if not reviews:
        return {"ok": True, "review": "No actionable findings"}

    final = await _call_openai(_build_merge_prompt(reviews), MAX_TOKENS)

    mandatory = _has_critical(final)
    body = AI_NOTE_MARKER + "\n\n" + final

    mr.notes.create({"body": body})

    return {
        "ok": True,
        "mandatory_approval": mandatory,
        "tokens_used": tracker.total
    }

# -------------------- HEALTH --------------------

@app.get("/")
def root():
    return {"ok": True, "service": "GitLab AI MR Bot"}
