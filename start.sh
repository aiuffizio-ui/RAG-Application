#!/bin/bash

# Quick start script for local development

echo "🚀 Starting Uffizio RAG Application..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "📝 Please copy .env.example to .env and add your GEMINI_API_KEY"
    exit 1
fi

# Check for GEMINI_API_KEY
source .env
if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ GEMINI_API_KEY not set in .env!"
    echo "📝 Please add your Gemini API key to .env"
    exit 1
fi

echo "✅ Environment configured"

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "📦 Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
else
    echo "✅ Virtual environment found"
fi

# Move knowledge file if needed
if [ ! -f "data/uffizio_knowledge.txt" ] && [ -f "uffizio_knowledge.txt" ]; then
    echo "📁 Moving knowledge file to data directory..."
    cp uffizio_knowledge.txt data/
fi

# Start backend
echo "🔧 Starting backend..."
cd backend
source venv/bin/activate
python -m app.main &
BACKEND_PID=$!
cd ..

echo "⏳ Waiting for backend to start..."
sleep 5

# Check if backend is running
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ Backend is running!"
else
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Ask user if they want to run ingestion
echo ""
echo "📊 Do you want to run data ingestion now? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "🔄 Running ingestion..."
    curl -X POST http://localhost:8000/api/ingest \
        -H "x-api-key: $ADMIN_API_KEY" \
        -H "Content-Type: application/json"
    echo ""
    echo "✅ Ingestion complete!"
fi

echo ""
echo "✨ Backend is ready at http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "To start the frontend (requires Node.js):"
echo "  cd frontend && npm install && npm run dev"
echo ""
echo "Or use Docker: docker-compose up"
echo ""
echo "Press Ctrl+C to stop the backend"

# Wait for Ctrl+C
trap "echo ''; echo '🛑 Stopping backend...'; kill $BACKEND_PID 2>/dev/null; exit 0" INT
wait $BACKEND_PID
