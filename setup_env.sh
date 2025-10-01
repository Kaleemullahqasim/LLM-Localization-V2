#!/bin/bash

# Setup environment file for LLM Localization V2
# This script copies the example env file to .env if it doesn't exist

echo "🔧 Setting up environment configuration..."

BACKEND_DIR="$(dirname "$0")/backend"
ENV_FILE="$BACKEND_DIR/.env"
EXAMPLE_FILE="$BACKEND_DIR/env.example"

if [ ! -f "$ENV_FILE" ]; then
    if [ -f "$EXAMPLE_FILE" ]; then
        cp "$EXAMPLE_FILE" "$ENV_FILE"
        echo "✅ Created .env file from env.example"
        echo ""
        echo "📝 IMPORTANT: Edit backend/.env to configure your models:"
        echo "   CHAT_MODEL=your-chat-model-name"
        echo "   EMBED_MODEL=your-embedding-model-name"
        echo ""
    else
        echo "❌ Error: env.example file not found"
        exit 1
    fi
else
    echo "ℹ️  .env file already exists"
    echo ""
    echo "📝 Current configuration:"
    grep "^CHAT_MODEL=" "$ENV_FILE" || echo "   CHAT_MODEL not found"
    grep "^EMBED_MODEL=" "$ENV_FILE" || echo "   EMBED_MODEL not found"
    echo ""
    echo "To change models, edit: backend/.env"
fi

echo ""
echo "🎯 Next steps:"
echo "   1. Make sure LM Studio is running with your models"
echo "   2. Run: cd backend && python start.py"
echo "   3. Run: cd frontend && npm run dev"

