#!/usr/bin/env python3
"""Simple test to verify LM Studio connection"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append('/Users/kaleemullahqasim/Documents/GitHub/LLM-Localization-V2/backend')

from app.services.lm_studio_client import LMStudioClient

async def test_basic_connection():
    """Test basic LM Studio connection"""
    print("🔌 Testing LM Studio Client...")
    
    client = LMStudioClient()
    print(f"Chat URL: {client.chat_base_url}")
    print(f"Embed URL: {client.embed_base_url}")
    print(f"Chat Model: {client.chat_model}")
    print(f"Embed Model: {client.embed_model}")
    
    try:
        # Test embeddings first (simpler)
        print("\n📊 Testing embeddings...")
        embeddings = await client.get_embeddings(["Hello world"])
        print(f"✅ Embeddings worked! Shape: {len(embeddings[0])}")
        
        # Test chat completion
        print("\n💬 Testing chat completion...")
        messages = [{"role": "user", "content": "Say hello"}]
        response = await client.chat_completion(messages)
        print(f"✅ Chat completion worked! Response: {response['choices'][0]['message']['content'][:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_basic_connection())
    sys.exit(0 if success else 1)