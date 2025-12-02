import logging
from typing import List, AsyncGenerator, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from app.core.config import settings

logger = logging.getLogger(__name__)

class RAGEngine:
    _instance: Optional['RAGEngine'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GENERATION_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.2,
            convert_system_message_to_human=True
        )
        
        self.prompt_template = PromptTemplate(
            template="""Use the following pieces of context to answer the question at the end. 
If you don't know the answer, just say that you don't know, don't try to make up an answer.
Keep the answer concise and helpful.

Context:
{context}

Question: {question}

Answer:""",
            input_variables=["context", "question"]
        )
        
        self.chain = self.prompt_template | self.llm

    async def generate(self, query: str, context_docs: List[Document], stream: bool = False):
        context_text = "\n\n".join([doc.page_content for doc in context_docs])
        
        if not context_docs:
            # Fallback if no docs? Or just answer?
            # User requirement: "if generation fails, return top-3 retrieved passages as fallback."
            # This implies we try to generate, if exception, return docs.
            pass

        try:
            if stream:
                return self._stream_response(query, context_text)
            else:
                response = await self.chain.ainvoke({"context": context_text, "question": query})
                return response.content
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            # Fallback strategy handled by caller usually, but we can return specific signal
            raise e

    async def _stream_response(self, query: str, context_text: str) -> AsyncGenerator[str, None]:
        async for chunk in self.chain.astream({"context": context_text, "question": query}):
            yield chunk.content

def get_rag_engine() -> RAGEngine:
    """Get or create the RAG engine instance (lazy initialization)."""
    return RAGEngine()
