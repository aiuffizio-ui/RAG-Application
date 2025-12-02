import logging
import os
from typing import List, Tuple
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from rank_bm25 import BM25Okapi
from app.core.config import settings

logger = logging.getLogger(__name__)

class HybridRetriever:
    def __init__(self):
        from langchain_community.embeddings import HuggingFaceEmbeddings

        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.index_path = os.path.join(settings.DATA_DIR, "faiss_index")
        self.vector_store = None
        self.bm25 = None
        self.chunk_id_to_index = {} # Map chunk_id to index in self.documents
        self.load_index()

    def load_index(self):
        if os.path.exists(self.index_path):
            try:
                self.vector_store = FAISS.load_local(self.index_path, self.embeddings, allow_dangerous_deserialization=True)
                
                # Extracting from vector store docstore
                self.documents = list(self.vector_store.docstore._dict.values())
                # Create mapping from chunk_id to index
                self.chunk_id_to_index = {doc.metadata.get("chunk_id"): i for i, doc in enumerate(self.documents)}
                
                tokenized_corpus = [doc.page_content.split() for doc in self.documents]
                self.bm25 = BM25Okapi(tokenized_corpus)
                logger.info("Index and BM25 loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load index: {e}")
        else:
            logger.warning("No index found. Ingestion needed.")

    def search(self, query: str, top_k: int = 8, alpha: float = 0.7) -> List[Document]:
        if not self.vector_store or not self.bm25:
            self.load_index()
            if not self.vector_store:
                return []

        # 1. Vector Search (get more than k to rerank)
        vector_docs_with_scores = self.vector_store.similarity_search_with_score(query, k=top_k * 2)
        
        # 2. BM25 Score
        tokenized_query = query.split()
        
        combined_results = []
        
        for doc, vector_score in vector_docs_with_scores:
            # Calculate BM25 score for this doc
            chunk_id = doc.metadata.get("chunk_id")
            doc_index = self.chunk_id_to_index.get(chunk_id)
            
            if doc_index is not None:
                # get_batch_scores takes list of query tokens and list of doc indices
                lexical_score = self.bm25.get_batch_scores(tokenized_query, [doc_index])[0]
            else:
                logger.warning(f"Chunk ID {chunk_id} not found in BM25 index")
                lexical_score = 0.0
            
            # Normalize scores? Vector score (L2) is 0 to infinity. 
            # If using Cosine, it's 0-1.
            # Let's assume we want to combine them.
            # Simple weighted sum.
            
            # Note: FAISS L2 distance: 0 is identical.
            # We want similarity. Sim = 1 / (1 + distance)
            similarity = 1 / (1 + vector_score)
            
            final_score = (alpha * similarity) + ((1 - alpha) * lexical_score)
            
            # Attach score to metadata
            doc.metadata["score"] = float(final_score)
            combined_results.append((doc, final_score))
            
        # Sort by final score
        combined_results.sort(key=lambda x: x[1], reverse=True)
        
        return [doc for doc, score in combined_results[:top_k]]

retriever = HybridRetriever()
