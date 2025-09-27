#!/usr/bin/env python3
"""Debug httpx connection to LM Studio"""

import asyncio
import httpx
import json

async def test_httpx_direct():
    """Test httpx connection directly"""
    print("🔌 Direct httpx test...")
    
    payload = {
        "model": "qwen/qwen3-1.7b",
        "messages": [{"role": "user", "content": "Hello"}],
        "temperature": 0.1,
        "max_tokens": 50,
        "stream": False
    }
    
    try:
        # Test with different configurations
        print("Testing with default client...")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:1234/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30.0
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"Default client failed: {e}")
    
    try:
        print("\nTesting with no keep-alive...")
        async with httpx.AsyncClient(http2=False) as client:
            response = await client.post(
                "http://localhost:1234/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Connection": "close"
                },
                json=payload,
                timeout=30.0
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"No keep-alive client failed: {e}")
    
    try:
        print("\nTesting with limits...")
        limits = httpx.Limits(max_keepalive_connections=0, max_connections=1)
        async with httpx.AsyncClient(limits=limits) as client:
            response = await client.post(
                "http://localhost:1234/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30.0
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"Limited client failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_httpx_direct())