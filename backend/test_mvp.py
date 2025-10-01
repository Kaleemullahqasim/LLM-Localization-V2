#!/usr/bin/env python3
"""
Simple test script to verify the MVP is working
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.lm_studio_client import LMStudioClient
from app.services.embedding_service import EmbeddingService
from app.models import Rule, MacroClass, Severity, Citation

async def test_lm_studio_connection():
    """Test connection to LM Studio"""
    print("🔌 Testing LM Studio connection...")
    
    client = LMStudioClient()
    
    try:
        # Test chat completion
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello MVP' if you can hear me."}
        ]
        
        response = await client.chat_completion(messages)
        chat_content = response["choices"][0]["message"]["content"]
        print(f"✅ Chat model response: {chat_content}")
        
        # Test embeddings
        embeddings = await client.get_embeddings(["Hello world", "Test embedding"])
        print(f"✅ Embeddings working: {len(embeddings)} vectors, dimension {len(embeddings[0])}")
        
        return True
        
    except Exception as e:
        print(f"❌ LM Studio connection failed: {e}")
        return False

async def test_rule_extraction():
    """Test rule extraction from text"""
    print("\n🔍 Testing rule extraction...")
    
    client = LMStudioClient()
    
    sample_text = """
    5.5 Punctuation Guidelines
    
    You must use full-width punctuation marks in Simplified Chinese.
    
    Correct: 你好！
    Wrong: 你好!
    
    Never use half-width exclamation marks in Chinese text.
    """
    
    try:
        rules = await client.extract_rules_from_text(sample_text, ["5", "5.5"])
        print(f"✅ Extracted {len(rules)} rules:")
        for i, rule in enumerate(rules, 1):
            print(f"   {i}. {rule.get('rule_text', 'N/A')}")
            
        return len(rules) > 0
        
    except Exception as e:
        print(f"❌ Rule extraction failed: {e}")
        return False

async def test_evaluation():
    """Test translation evaluation"""
    print("\n📝 Testing translation evaluation...")
    
    client = LMStudioClient()
    
    # Create a mock rule for testing
    candidate_rules = [{
        'rule_id': 'TEST-PUNCT-001',
        'rule_text': 'Use full-width exclamation marks in Chinese',
        'examples_pos': ['你好！'],
        'examples_neg': ['你好!']
    }]
    
    try:
        findings = await client.evaluate_translation(
            source_text="Hello!",
            target_text="你好!",  # Wrong punctuation
            candidate_rules=candidate_rules,
            locale="zh-CN"
        )
        
        print(f"✅ Evaluation found {len(findings)} issues:")
        for finding in findings:
            print(f"   - {finding.get('justification', 'N/A')}")
            
        return True
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        return False

async def test_directory_structure():
    """Test that all required directories and files exist"""
    print("\n📁 Testing directory structure...")
    
    required_dirs = [
        "data/uploads",
        "data/knowledge_bases", 
        "data/evaluations",
        "data/embeddings",
        "data/feedback"
    ]
    
    required_files = [
        "app/main.py",
        "app/models/__init__.py",
        "app/services/lm_studio_client.py",
        "app/services/document_ingestion.py",
        "app/services/evaluation_engine.py",
        "requirements.txt",
        ".env"
    ]
    
    all_good = True
    
    for directory in required_dirs:
        if not os.path.exists(directory):
            print(f"❌ Missing directory: {directory}")
            all_good = False
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"✅ Directory exists: {directory}")
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ Missing file: {file_path}")
            all_good = False
        else:
            print(f"✅ File exists: {file_path}")
    
    return all_good

async def main():
    """Run all tests"""
    print("🧪 MVP System Test Suite")
    print("=" * 40)
    
    # Test 1: Directory structure
    test1 = await test_directory_structure()
    
    # Test 2: LM Studio connection
    test2 = await test_lm_studio_connection()
    
    if test2:
        # Test 3: Rule extraction (only if LM Studio is working)
        test3 = await test_rule_extraction()
        
        # Test 4: Evaluation (only if LM Studio is working)  
        test4 = await test_evaluation()
    else:
        test3 = test4 = False
        print("⚠️  Skipping LLM tests due to connection failure")
    
    # Summary
    print("\n📊 Test Results:")
    print("=" * 40)
    print(f"Directory Structure: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"LM Studio Connection: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"Rule Extraction: {'✅ PASS' if test3 else '❌ FAIL'}")
    print(f"Translation Evaluation: {'✅ PASS' if test4 else '❌ FAIL'}")
    
    if all([test1, test2, test3, test4]):
        print("\n🎉 All tests passed! Your MVP is ready.")
        print("\nNext steps:")
        print("1. Run: python start.py")
        print("2. Upload a style guide via API")
        print("3. Test evaluation endpoints")
    else:
        print("\n⚠️  Some tests failed. Check the issues above.")
        if not test2:
            print("\n💡 Make sure LM Studio is running with the configured models:")
            print(f"   - Chat model: {os.getenv('CHAT_MODEL', 'qwen/qwen3-1.7b')} on {os.getenv('CHAT_BASE_URL', 'http://localhost:1234/v1')}")
            print(f"   - Embedding model: {os.getenv('EMBED_MODEL', 'text-embedding-qwen3-embedding-8b')} on {os.getenv('EMBED_BASE_URL', 'http://127.0.0.1:1234/v1')}")

if __name__ == "__main__":
    asyncio.run(main())