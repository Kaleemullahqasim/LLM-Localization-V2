#!/usr/bin/env python3
"""
Startup script for the Rule-Anchored Localization QA System
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("🚀 Starting Rule-Anchored Localization QA System")
    print("=" * 50)
    
    # Check if we're in the backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Check if virtual environment exists
    venv_path = backend_dir / "venv"
    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"])
    
    # Determine pip path
    if sys.platform == "win32":
        pip_path = venv_path / "Scripts" / "pip"
        python_path = venv_path / "Scripts" / "python"
    else:
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"
    
    # Install requirements
    print("📚 Installing dependencies...")
    subprocess.run([str(pip_path), "install", "-r", "requirements.txt"])
    
    # Create data directories
    print("📁 Creating data directories...")
    os.makedirs("data/uploads", exist_ok=True)
    os.makedirs("data/knowledge_bases", exist_ok=True)
    os.makedirs("data/evaluations", exist_ok=True)
    os.makedirs("data/embeddings", exist_ok=True)
    os.makedirs("data/feedback", exist_ok=True)
    
    # Check .env file
    env_file = backend_dir / ".env"
    if not env_file.exists():
        print("⚠️  .env file not found! Creating default...")
        with open(env_file, "w") as f:
            f.write("""# LM Studio Configuration
CHAT_BASE_URL=http://localhost:1234/v1
CHAT_MODEL=qwen/qwen3-1.7b
EMBED_BASE_URL=http://127.0.0.1:1234/v1
EMBED_MODEL=text-embedding-qwen3-embedding-8b

# Scoring Configuration  
SEVERITY_MULTIPLIER_MINOR=1
SEVERITY_MULTIPLIER_MAJOR=2
SEVERITY_MULTIPLIER_CRITICAL=3
STYLE_PUNCTUATION_CAP=30

# Default Weights by Macro Class
WEIGHT_ACCURACY=5
WEIGHT_TERMINOLOGY=4
WEIGHT_MECHANICS=3
WEIGHT_PUNCTUATION=2
WEIGHT_STYLE=1
WEIGHT_LEGAL=6
WEIGHT_STANDARDS=3

# Application Settings
DEBUG=true
DATA_DIR=./data
UPLOAD_MAX_SIZE=10485760
""")
    
    print("✅ Setup complete!")
    print("\n🔧 Make sure LM Studio is running with the configured models:")
    print(f"   - Chat model: {os.getenv('CHAT_MODEL', 'qwen/qwen3-1.7b')} on {os.getenv('CHAT_BASE_URL', 'http://localhost:1234/v1')}")
    print(f"   - Embedding model: {os.getenv('EMBED_MODEL', 'text-embedding-qwen3-embedding-8b')} on {os.getenv('EMBED_BASE_URL', 'http://127.0.0.1:1234/v1')}")
    print("\n🚀 Starting FastAPI server...")
    
    # Start the server
    subprocess.run([
        str(python_path), "-m", "uvicorn", 
        "app.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000", 
        "--reload"
    ])

if __name__ == "__main__":
    main()