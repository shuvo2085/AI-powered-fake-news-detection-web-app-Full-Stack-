#!/bin/bash
# TruthLens startup script

echo "╔═══════════════════════════════════════╗"
echo "║       TruthLens — Fake News Detector  ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3."
    exit 1
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r backend/requirements.txt -q

# Check MongoDB
if ! command -v mongod &> /dev/null; then
    echo "⚠️  MongoDB not found locally. Make sure it's installed or use MONGO_URI env variable."
else
    echo "✅ MongoDB found"
fi

echo ""
echo "🚀 Starting API server on http://localhost:5000"
echo "📂 Open frontend/index.html in your browser"
echo "⌨️  Press Ctrl+C to stop"
echo ""

cd backend && python3 app.py
