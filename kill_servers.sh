#!/bin/bash

# Kill all running backend and frontend servers

echo "🛑 Stopping all servers..."

# Kill backend (uvicorn/FastAPI)
echo "Stopping backend servers..."
pkill -f "uvicorn app.main:app" 2>/dev/null
pkill -f "python.*start.py" 2>/dev/null
pkill -f "fastapi" 2>/dev/null

# Kill frontend (Vite/npm)
echo "Stopping frontend servers..."
pkill -f "vite" 2>/dev/null
pkill -f "npm run dev" 2>/dev/null

# Kill any process using port 8000 (backend)
echo "Checking port 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null

# Kill any process using port 3000 (frontend)
echo "Checking port 3000..."
lsof -ti:3000 | xargs kill -9 2>/dev/null

echo "✅ All servers stopped"
echo ""
echo "You can now restart with:"
echo "   cd backend && python start.py"
echo "   cd frontend && npm run dev"

