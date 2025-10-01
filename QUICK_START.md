# 🚀 Quick Start Guide

## ✅ Your System is Now Configured!

The centralized configuration is set up and ready to use.

---

## 📍 **WHERE TO CHANGE MODELS**

### **ONLY edit this file:** `backend/.env`

```bash
# Open the file
nano backend/.env
# or
code backend/.env
```

### **Change ONLY these two lines:**
```bash
CHAT_MODEL=baidu/ernie-4.5-21b-a3b
EMBED_MODEL=text-embedding-qwen3-embedding-8b:2
```

**That's it!** The system will automatically use these models everywhere.

---

## 🎯 Common Tasks

### **1. Kill All Servers** (if Ctrl+C doesn't work)
```bash
./kill_servers.sh
```

### **2. Start Backend**
```bash
cd backend
python start.py
```

### **3. Start Frontend** (in a new terminal)
```bash
cd frontend
npm run dev
```

### **4. Change Models**
```bash
# 1. Edit the .env file
nano backend/.env

# 2. Kill servers
./kill_servers.sh

# 3. Restart backend
cd backend && python start.py
```

### **5. Check Current Configuration**
```bash
cd backend
source venv/bin/activate
python -c "from app.config import config; print('Chat:', config.CHAT_MODEL); print('Embed:', config.EMBED_MODEL)"
```

---

## 🔧 Fixing the Embedding Error

If you see **"embedding model error"** after rule extraction:

### **Step 1: Check LM Studio**
1. Open LM Studio
2. Go to "Local Server" tab
3. Verify **BOTH** models are loaded and running:
   - ✅ Chat model: `baidu/ernie-4.5-21b-a3b`
   - ✅ Embedding model: `text-embedding-qwen3-embedding-8b:2`

### **Step 2: Verify Model Names Match**
The model name in `backend/.env` **MUST EXACTLY MATCH** the name in LM Studio.

**Common mistakes:**
- ❌ Missing version tag: `text-embedding-qwen3-embedding-8b` 
- ✅ Correct: `text-embedding-qwen3-embedding-8b:2`

**How to get the exact name:**
1. In LM Studio, find your embedding model
2. Copy the FULL name including `:version` if present
3. Paste into `backend/.env`:
   ```bash
   EMBED_MODEL=text-embedding-qwen3-embedding-8b:2
   ```

### **Step 3: Restart**
```bash
./kill_servers.sh
cd backend && python start.py
```

---

## 📊 Testing the System

### **Test 1: Upload a Document**
1. Open http://localhost:3000
2. Go to "Upload Style Guide" tab
3. Upload a DOCX/PDF file
4. Watch the terminal for progress

**If it fails at embedding:**
- Check LM Studio server is running
- Check both models are loaded
- Check model names match exactly

### **Test 2: Evaluate Translation**
1. Go to "Evaluate Translation" tab
2. Enter source and target text
3. Select a Knowledge Base
4. Click "Evaluate"

---

## 🐛 Troubleshooting

### **Problem: "Cannot connect to model"**
**Fix:** Start LM Studio server with both models loaded

### **Problem: "Port 8000 already in use"**
**Fix:** `./kill_servers.sh`

### **Problem: "Embedding model not found"**
**Fix:** Check the model name in LM Studio and copy it EXACTLY to `.env`

### **Problem: "Module not found"**
**Fix:** Activate virtual environment:
```bash
cd backend
source venv/bin/activate
```

---

## 📁 Important Files

| File | Purpose | Edit? |
|------|---------|-------|
| `backend/.env` | **Model configuration** | ✅ **YES** |
| `backend/app/config.py` | Reads .env file | ❌ NO |
| `CONFIG_GUIDE.md` | Detailed guide | 📖 READ |
| `kill_servers.sh` | Stop servers | ▶️ RUN |
| `setup_env.sh` | First-time setup | ▶️ RUN ONCE |

---

## 🎬 Complete Workflow

```bash
# 1. Kill any running servers
./kill_servers.sh

# 2. Check your configuration
cd backend && source venv/bin/activate && python -c "from app.config import config; print(config)"

# 3. Make sure LM Studio is running with both models

# 4. Start backend (Terminal 1)
cd backend && python start.py

# 5. Start frontend (Terminal 2)
cd frontend && npm run dev

# 6. Open browser
# http://localhost:3000
```

---

## ⚡ Quick Reference

```bash
# View current models
cat backend/.env | grep MODEL

# Change models
nano backend/.env

# Restart system
./kill_servers.sh && cd backend && python start.py &
cd frontend && npm run dev

# Check logs
tail -f backend/data/evaluations/*.json
```

---

## 📞 Need Help?

1. Read: `CONFIG_GUIDE.md` (detailed troubleshooting)
2. Check: Backend terminal for error messages
3. Verify: LM Studio server status
4. Test: Model names match exactly

---

## ✨ Key Points

1. **Only edit** `backend/.env` to change models
2. **Exact model names** from LM Studio are required
3. **Both models** must be loaded in LM Studio
4. **Use `./kill_servers.sh`** if Ctrl+C doesn't work
5. **Restart backend** after changing .env

