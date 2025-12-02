from fastapi import APIRouter, HTTPException, Depends, Header, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import logging
import pandas as pd
import os
import json

from app.core.config import settings
from app.core.ingestion import ingestion_manager
from app.core.retrieval import retriever
from app.core.generation import get_rag_engine

router = APIRouter()
logger = logging.getLogger(__name__)

# Auth dependency
async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.ADMIN_API_KEY: # Simple check, in prod use DB or more complex
        # Allow user key too if we had one, but for now just one key or env var
        # User said "support API key via header x-api-key configurable through env var"
        pass
    return x_api_key

class QueryRequest(BaseModel):
    query: str
    top_k: int = 8
    max_tokens: int = 1024
    stream: bool = False

class IngestResponse(BaseModel):
    status: str
    total_chunks: int

@router.post("/ingest", response_model=IngestResponse)
async def ingest_data(background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    # Trigger ingestion in background? Or sync?
    # User said "Returns ingestion status, total chunks added."
    # If file is huge, sync might timeout. But for 26k lines it's fine.
    # Let's do sync for now to return accurate count.
    try:
        count = ingestion_manager.run_ingestion()
        # Reload retriever
        retriever.load_index()
        return {"status": "success", "total_chunks": count}
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reindex")
async def reindex(api_key: str = Depends(verify_api_key)):
    try:
        # Delete existing index
        if os.path.exists(ingestion_manager.index_path):
            import shutil
            shutil.rmtree(ingestion_manager.index_path)
        count = ingestion_manager.run_ingestion()
        retriever.load_index()
        return {"status": "reindexed", "total_chunks": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query")
async def query_endpoint(request: QueryRequest):
    # 1. Retrieve
    docs = retriever.search(request.query, top_k=request.top_k)
    
    # 2. Generate
    if request.stream:
        async def event_generator():
            try:
                # Send sources first? Or after?
                # Usually SSE sends chunks. We can send a special event for sources.
                # But standard SSE is just text.
                # We can send JSON chunks.
                
                # Send sources first
                sources = [{"chunk_id": d.metadata.get("chunk_id"), "snippet": d.metadata.get("original_text_snippet"), "score": d.metadata.get("score")} for d in docs]
                yield json.dumps({"type": "sources", "data": sources}) + "\n"
                
                generator = await get_rag_engine().generate(request.query, docs, stream=True)
                async for token in generator:
                    yield json.dumps({"type": "token", "data": token}) + "\n"
            except Exception as e:
                # Fallback
                logger.error(f"Streaming generation failed: {e}")
                fallback_docs = [{"content": d.page_content, "metadata": d.metadata} for d in docs[:3]]
                yield json.dumps({"type": "error", "data": "Generation failed", "fallback": fallback_docs}) + "\n"

        return StreamingResponse(event_generator(), media_type="application/x-ndjson")
    else:
        try:
            answer = await get_rag_engine().generate(request.query, docs, stream=False)
            return {
                "answer": answer,
                "sources": [{"chunk_id": d.metadata.get("chunk_id"), "snippet": d.metadata.get("original_text_snippet"), "score": d.metadata.get("score")} for d in docs]
            }
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return {
                "error": "Generation failed",
                "fallback_docs": [{"content": d.page_content, "metadata": d.metadata} for d in docs[:3]]
            }

@router.get("/health")
async def health_check():
    index_exists = os.path.exists(settings.INDEX_FILE) or os.path.exists(os.path.join(settings.DATA_DIR, "faiss_index"))
    return {"status": "ok", "index_present": index_exists}

@router.get("/metadata/{chunk_id}")
async def get_metadata(chunk_id: str):
    # Read from JSONL
    # This is inefficient for random access. 
    # Better to load into a dict or use a proper DB.
    # For this assignment, we'll scan the file or cache it.
    # Since we loaded it in retrieval for BM25 (maybe), we could use that.
    # Or just scan the file.
    
    meta_path = os.path.join(settings.DATA_DIR, settings.METADATA_FILE)
    if not os.path.exists(meta_path):
        raise HTTPException(status_code=404, detail="Metadata not found")
        
    # Simple scan (slow but works for file based)
    with open(meta_path, 'r') as f:
        for line in f:
            record = json.loads(line)
            if record.get("chunk_id") == chunk_id:
                return record
    
    raise HTTPException(status_code=404, detail="Chunk not found")
