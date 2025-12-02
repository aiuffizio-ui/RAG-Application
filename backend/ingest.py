"""
Simple script to run ingestion
Usage: python ingest.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.ingestion import ingestion_manager

if __name__ == "__main__":
    print("Starting ingestion...")
    try:
        count = ingestion_manager.run_ingestion()
        print(f"✅ Ingestion complete! Created {count} chunks")
        print(f"📂 Index saved to: {ingestion_manager.index_path}")
        print(f"📄 Metadata saved to: {ingestion_manager.metadata_path}")
    except Exception as e:
        print(f"❌ Ingestion failed: {e}")
        sys.exit(1)
