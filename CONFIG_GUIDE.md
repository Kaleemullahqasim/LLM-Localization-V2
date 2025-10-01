# Configuration Guide

## 🎯 Quick Start - Changing Models

### The ONLY file you need to edit: `backend/.env`

To change your LLM models, edit just TWO lines in the `.env` file:

```bash
CHAT_MODEL=your-chat-model-name
EMBED_MODEL=your-embedding-model-name
```

**Example:**
```bash
CHAT_MODEL=baidu/ernie-4.5-21b-a3b
EMBED_MODEL=text-embedding-qwen3-embedding-8b:2
```

### Setting Up for the First Time

1. **Create your `.env` file:**
   ```bash
   ./setup_env.sh
   ```

2. **Edit the model names** in `backend/.env`:
   ```bash
   nano backend/.env
   # or
   code backend/.env
   ```

3. **Make sure your models are loaded in LM Studio**

4. **Restart the backend:**
   ```bash
   ./kill_servers.sh
   cd backend && python start.py
   ```

---

## 🚨 Troubleshooting

### Problem: "Embedding model error" after rule extraction

**Symptoms:**
- Chat model (Baidu/Ernie) finishes extracting rules
- System fails when creating embeddings
- Error mentions embedding model

**Common Causes:**
1. Model name mismatch in LM Studio
2. Embedding model not loaded
3. Wrong port configuration

**Solution:**

1. **Check LM Studio:**
   - Open LM Studio
   - Go to "Local Server"
   - Verify BOTH models are loaded:
     - ✅ Chat model: `baidu/ernie-4.5-21b-a3b`
     - ✅ Embedding model: `text-embedding-qwen3-embedding-8b:2`

2. **Check the exact model names:**
   - In LM Studio, copy the EXACT model name (including version)
   - Paste into `backend/.env`:
     ```bash
     EMBED_MODEL=text-embedding-qwen3-embedding-8b:2
     ```

3. **Check ports:**
   - Default: Both models use `http://localhost:1234/v1`
   - If you changed ports in LM Studio, update `backend/.env`:
     ```bash
     CHAT_BASE_URL=http://localhost:YOUR_PORT/v1
     EMBED_BASE_URL=http://localhost:YOUR_PORT/v1
     ```

4. **Restart everything:**
   ```bash
   ./kill_servers.sh
   cd backend && python start.py
   ```

---

## 🛑 How to Kill Running Servers

If Ctrl+C doesn't work, use the kill script:

```bash
./kill_servers.sh
```

This will:
- Stop all backend processes (uvicorn, FastAPI)
- Stop all frontend processes (Vite, npm)
- Free ports 8000 and 3000

---

## 📁 Configuration File Locations

### Main Configuration (EDIT THIS):
- **`backend/.env`** ← Change model names here
  - `CHAT_MODEL=...`
  - `EMBED_MODEL=...`

### System Files (DON'T EDIT THESE):
- `backend/app/config.py` ← Reads from `.env`
- `backend/app/services/lm_studio_client.py` ← Uses config
- `backend/app/services/embedding_service.py` ← Uses config
- `backend/app/services/document_ingestion.py` ← Uses config
- `backend/app/services/evaluation_engine.py` ← Uses config

---

## 🔍 Verifying Your Configuration

Run this to see what models the system will use:

```bash
cd backend
source venv/bin/activate
python -c "from app.config import config; print('Chat Model:', config.CHAT_MODEL); print('Embed Model:', config.EMBED_MODEL)"
```

Expected output:
```
Chat Model: baidu/ernie-4.5-21b-a3b
Embed Model: text-embedding-qwen3-embedding-8b:2
```

---

## 🎬 Complete Workflow

### 1. Setup (First Time Only)
```bash
# Create .env file
./setup_env.sh

# Edit model names
nano backend/.env
```

### 2. Start Services
```bash
# Terminal 1: Backend
cd backend
python start.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

### 3. Stop Services
```bash
# Use Ctrl+C in each terminal
# OR if that doesn't work:
./kill_servers.sh
```

### 4. Change Models
```bash
# Edit the .env file
nano backend/.env

# Kill old servers
./kill_servers.sh

# Start new servers
cd backend && python start.py
cd frontend && npm run dev
```

---

## ⚡ Quick Commands

```bash
# Setup environment
./setup_env.sh

# Kill all servers
./kill_servers.sh

# Check configuration
cd backend && source venv/bin/activate && python -c "from app.config import config; print(config)"

# Restart backend
./kill_servers.sh && cd backend && python start.py

# View logs
cd backend && tail -f data/evaluations/*.json
```

---

## 🐛 Common Errors and Fixes

### Error: "Connection refused" or "Model not found"
**Fix:** Make sure LM Studio server is running and models are loaded

### Error: "Module 'app.config' not found"
**Fix:** Make sure you're in the virtual environment:
```bash
cd backend
source venv/bin/activate
```

### Error: "Port 8000 already in use"
**Fix:** Kill existing servers:
```bash
./kill_servers.sh
```

### Error: "Embedding model timeout"
**Fix:** 
1. Check LM Studio has enough VRAM
2. Try a smaller embedding model
3. Increase timeout in `.env`:
   ```bash
   TIMEOUT=300
   ```

---

## 📝 Model Name Format Examples

Different model loaders use different naming:

```bash
# With version tag
EMBED_MODEL=text-embedding-qwen3-embedding-8b:2

# Without version
EMBED_MODEL=text-embedding-qwen3-embedding-8b

# With organization
CHAT_MODEL=baidu/ernie-4.5-21b-a3b

# Simple name
CHAT_MODEL=llama-3-8b-instruct
```

**Pro Tip:** Copy the EXACT name from LM Studio's model list!

