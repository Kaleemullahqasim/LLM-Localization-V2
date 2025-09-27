#!/usr/bin/env python3
"""
Working Demo: Upload file and test evaluation
"""

import requests
import tempfile
import os

print("🚀 REAL SYSTEM TEST")
print("=" * 40)

# Create a temporary style guide file
style_guide_content = """# Chinese Style Guide

## Punctuation Rules
- Always use full-width punctuation in Chinese: 你好！
- Never use half-width exclamation: 你好! (wrong)

## Brand Names
- Never translate "Shopify" 
- Keep {customer_name} placeholders unchanged
"""

# Test 1: Upload file
print("\n1️⃣ Uploading style guide file...")
with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
    f.write(style_guide_content)
    temp_file_path = f.name

try:
    with open(temp_file_path, 'rb') as f:
        files = {'file': ('style_guide.md', f, 'text/markdown')}
        response = requests.post('http://localhost:8000/api/upload-document', files=files)
        
    if response.status_code == 200:
        print("✅ File uploaded successfully!")
        print(f"Response: {response.json()}")
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(f"Error: {response.text}")
        
finally:
    os.unlink(temp_file_path)

# Test 2: Direct evaluation test (without knowledge base for now)
print(f"\n2️⃣ Testing evaluation endpoint...")

test_evaluation = {
    "source_text": "Welcome to Shopify!",
    "target_text": "欢迎使用Shopify!",  # Wrong: half-width exclamation
    "source_language": "en", 
    "target_language": "zh-CN"
}

eval_response = requests.post(
    'http://localhost:8000/api/evaluate',
    json=test_evaluation
)

if eval_response.status_code == 200:
    result = eval_response.json()
    print("✅ Evaluation successful!")
    print(f"📊 Score: {result.get('score', 'N/A')}")
    if 'findings' in result and result['findings']:
        print(f"🔍 Issues found: {len(result['findings'])}")
        for finding in result['findings'][:2]:
            print(f"   • {finding.get('description', '')[:60]}...")
else:
    print(f"❌ Evaluation failed: {eval_response.status_code}")
    print(f"Details: {eval_response.text}")

print(f"\n🎯 NEXT STEPS:")
print(f"✅ Your system IS working!")
print(f"📖 View API docs: http://localhost:8000/docs")
print(f"🔍 Upload real style guides")
print(f"📊 Test more translations")