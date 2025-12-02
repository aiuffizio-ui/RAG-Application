# Uffizio RAG Application

A production-ready Retrieval-Augmented Generation (RAG) system built with FastAPI, LangChain, FAISS, and Google Gemini, with a modern React frontend.

## Features

- **Smart Ingestion**: Parses and chunks large text files with metadata extraction
- **Vector Search**: FAISS vector database with hybrid search (Vector + BM25)
- **AI Generation**: Google Gemini for embeddings and text generation
- **Streaming Support**: Real-time streaming responses in the UI
- **Modern UI**: Beautiful dark-themed chat interface with Tailwind CSS
- **Docker Ready**: Full containerization with docker-compose

## Prerequisites

- Python 3.9+
- Node.js 18+ (for frontend development)
- Docker & Docker Compose (for containerized deployment)
- Google Gemini API Key ([Get one here](https://ai.google.dev/))

## Quick Start

### 1. Clone and Setup

```bash
cd /home/uffizio/Desktop/RAG
cp .env.example .env
```

Edit `.env` and add your `GEMINI_API_KEY`.

### 2. Move Knowledge File

```bash
# The knowledge file should be in the data directory
# It's already there if you have uffizio_knowledge.txt in the root
```

### 3. Backend Setup (Local Development)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run the backend
python -m app.main
```

The backend will be available at `http://localhost:8000`

### 4. Run Ingestion

First, you need to ingest the knowledge file:

```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "x-api-key: secret-key"
```

This will:
- Parse `uffizio_knowledge.txt`
- Chunk the content
- Generate embeddings using Gemini
- Build FAISS index
- Save metadata to disk

### 5. Frontend Setup (Local Development)

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 6. Docker Deployment (Recommended)

```bash
# Build and run everything
docker-compose up --build

# Run in background
docker-compose up -d
```

Access:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

## API Endpoints

### Health Check
```bash
GET /api/health
```

### Ingest Data
```bash
POST /api/ingest
Header: x-api-key: <your-admin-key>
```

### Query (Non-Streaming)
```bash
POST /api/query
Content-Type: application/json

{
  "query": "How to configure Trakzee?",
  "top_k": 8,
  "max_tokens": 1024,
  "stream": false
}
```

### Query (Streaming)
```bash
POST /api/query
Content-Type: application/json

{
  "query": "How to configure Trakzee?",
  "top_k": 8,
  "stream": true
}
```

### Get Metadata
```bash
GET /api/metadata/{chunk_id}
```

### Force Reindex
```bash
POST /api/reindex
Header: x-api-key: <your-admin-key>
```

## Project Structure

```
RAG/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints.py      # API routes
│   │   ├── core/
│   │   │   ├── config.py         # Configuration
│   │   │   ├── ingestion.py      # Data ingestion & chunking
│   │   │   ├── retrieval.py      # FAISS + BM25 hybrid search
│   │   │   └── generation.py     # Gemini LLM wrapper
│   │   └── main.py               # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatInterface.jsx
│   │   │   ├── MessageBubble.jsx
│   │   │   ├── SourceDisplay.jsx
│   │   │   └── Settings.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── Dockerfile
├── data/
│   ├── uffizio_knowledge.txt     # Source knowledge base
│   ├── faiss_index/              # Generated FAISS index
│   └── metadata.jsonl            # Chunk metadata
├── docker-compose.yml
├── .env
└── README.md
```

## Configuration

### Backend Configuration (`backend/app/core/config.py`)

- `GEMINI_API_KEY`: Your Gemini API key
- `EMBEDDING_MODEL`: Default is `models/gemini-embedding-001`
- `GENERATION_MODEL`: Default is `gemini-pro`
- `CHUNK_SIZE`: Default 1000 characters
- `CHUNK_OVERLAP`: Default 200 characters
- `BATCH_SIZE`: Default 10 for rate limiting
- `TOP_K`: Default 8 retrieval results

### Frontend Settings

Available in the UI Settings panel:
- **API Key**: For authentication
- **Top K**: Number of retrieval results (1-20)
- **Streaming**: Enable/disable streaming responses
- **Debug Mode**: Show raw context and fallback docs

## Usage

1. **First Time Setup**: Run ingestion to build the index
2. **Query**: Use the chat interface to ask questions
3. **View Sources**: Expand source dropdown to see retrieved chunks
4. **Adjust Settings**: Tune top_k and other parameters

## Troubleshooting

### Backend won't start
- Check if `GEMINI_API_KEY` is set in `.env`
- Verify Python dependencies are installed
- Check port 8000 is available

### Ingestion fails
- Ensure `uffizio_knowledge.txt` is in the `data/` directory
- Check API key has sufficient quota
- Check disk space for index storage

### No results returned
- Verify index was created (check `data/faiss_index/`)
- Run health check: `curl http://localhost:8000/api/health`
- Try reindexing: `POST /api/reindex`

### Frontend can't connect
- Check backend is running on port 8000
- Verify `VITE_API_URL` in `.env`
- Check CORS settings in `backend/app/main.py`

## Performance Tips

- **Use Docker**: Simplifies deployment and dependency management
- **Batch Size**: Adjust based on API rate limits
- **Index Type**: Switch from Flat to IVF for larger datasets
- **Caching**: Consider adding Redis for frequent queries

## License

MIT

## Support

For issues or questions, contact Uffizio support or raise an issue on GitHub.
