import os
import json
import time
import logging
from typing import List, Dict, Any
import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings


from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from app.core.config import settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IngestionManager:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.vector_store = None
        self.metadata_path = os.path.join(settings.DATA_DIR, settings.METADATA_FILE)
        self.index_path = os.path.join(settings.DATA_DIR, "faiss_index")

    def load_file(self, file_path: str) -> List[Dict[str, Any]]:
        logger.info(f"Loading file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by delimiter
        raw_docs = content.split("================================================================================")
        processed_docs = []
        
        for raw_doc in raw_docs:
            if not raw_doc.strip():
                continue
            
            lines = raw_doc.strip().split('\n')
            title = "Unknown"
            url = "Unknown"
            body_lines = []
            
            for line in lines:
                if line.startswith("Title:"):
                    title = line.replace("Title:", "").strip()
                elif line.startswith("URL:"):
                    url = line.replace("URL:", "").strip()
                else:
                    body_lines.append(line)
            
            body = "\n".join(body_lines).strip()
            if body:
                processed_docs.append({
                    "title": title,
                    "url": url,
                    "content": body
                })
        
        logger.info(f"Parsed {len(processed_docs)} documents")
        return processed_docs

    def chunk_documents(self, docs: List[Dict[str, Any]]) -> List[Document]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        
        chunked_docs = []
        chunk_id_counter = 0
        
        for doc in docs:
            chunks = splitter.split_text(doc["content"])
            for i, chunk in enumerate(chunks):
                chunk_id = f"chunk_{chunk_id_counter}"
                metadata = {
                    "source_file": settings.KNOWLEDGE_FILE,
                    "chunk_id": chunk_id,
                    "title": doc["title"],
                    "url": doc["url"],
                    "start_pos": -1, # generic, hard to track exact pos after split
                    "end_pos": -1,
                    "original_text_snippet": chunk[:200]
                }
                chunked_docs.append(Document(page_content=chunk, metadata=metadata))
                chunk_id_counter += 1
                
        logger.info(f"Created {len(chunked_docs)} chunks")
        return chunked_docs

    def batch_embed_and_index(self, documents: List[Document]):
        total_docs = len(documents)
        batch_size = settings.BATCH_SIZE
        
        # Check if index exists to load it, else create new
        if os.path.exists(self.index_path):
             logger.info("Loading existing FAISS index...")
             self.vector_store = FAISS.load_local(self.index_path, self.embeddings, allow_dangerous_deserialization=True)
        else:
             logger.info("Creating new FAISS index...")
             # Initialize with first batch
             first_batch = documents[:batch_size]
             self.vector_store = FAISS.from_documents(first_batch, self.embeddings)
             documents = documents[batch_size:]

        # Process remaining in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            logger.info(f"Embedding batch {i//batch_size + 1}/{(len(documents)//batch_size) + 1}")
            try:
                self.vector_store.add_documents(batch)
                # Checkpoint every 10 batches
                if (i // batch_size) % 10 == 0:
                     self.vector_store.save_local(self.index_path)
                time.sleep(1) # Rate limit buffer
            except Exception as e:
                logger.error(f"Error embedding batch: {e}")
                # Continue or retry logic could go here
        
        # Final save
        self.vector_store.save_local(self.index_path)
        
        # Save metadata separately for audit
        meta_records = [doc.metadata for doc in documents]
        # Append to existing if needed, but for now overwrite/new
        df = pd.DataFrame(meta_records)
        df.to_json(self.metadata_path, orient='records', lines=True)
        logger.info("Ingestion complete")

    def run_ingestion(self, file_path: str = None):
        if not file_path:
            file_path = os.path.join(settings.DATA_DIR, settings.KNOWLEDGE_FILE)
            
        docs = self.load_file(file_path)
        chunks = self.chunk_documents(docs)
        self.batch_embed_and_index(chunks)
        return len(chunks)

ingestion_manager = IngestionManager()
