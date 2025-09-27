#!/usr/bin/env python3
"""
Simple Demo: Show exactly what the system does
"""

import requests
import json
import time

print("🚀 LIVE DEMO: Rule-Anchored Localization QA System")
print("=" * 60)

# Step 1: Upload a style guide
print("\n1️⃣ UPLOADING A CHINESE STYLE GUIDE...")
style_guide = """
# Shopify Chinese Style Guide

## Punctuation Rules
1. Always use full-width punctuation in Chinese: 你好！欢迎！
2. Never use half-width exclamation marks: 你好! ❌ (wrong)

## Brand Names  
3. Never translate "Shopify" - keep it as "Shopify"
4. Keep placeholder variables like {customer_name} unchanged

## Date Format
5. Use Chinese format: 2024年1月15日 (not 2024/01/15)
"""

upload_response = requests.post(
    "http://localhost:8000/api/upload-document",
    json={
        "content": style_guide,
        "filename": "shopify_chinese_guide.md", 
        "document_type": "markdown"
    }
)

if upload_response.status_code == 200:
    result = upload_response.json()
    kb_id = result.get("knowledge_base_id")
    print(f"✅ Style guide uploaded!")
    print(f"   📋 Knowledge Base ID: {kb_id}")
    print(f"   📝 Rules extracted: {len(result.get('summary', {}).get('extracted_rules', []))}")
    
    # Show some extracted rules
    rules = result.get('summary', {}).get('extracted_rules', [])
    if rules:
        print(f"   🎯 Example rule: {rules[0].get('description', '')[:60]}...")
else:
    print(f"❌ Upload failed: {upload_response.status_code} - {upload_response.text}")
    exit(1)

time.sleep(2)

# Step 2: Test some translations
print(f"\n2️⃣ TESTING TRANSLATIONS...")

test_cases = [
    {
        "name": "✅ GOOD Translation", 
        "source": "Welcome to Shopify!",
        "target": "欢迎使用Shopify！",  # Correct: full-width punctuation, Shopify not translated
    },
    {
        "name": "❌ BAD Translation",
        "source": "Welcome to Shopify!", 
        "target": "欢迎使用购物化!",  # Wrong: half-width punctuation, Shopify translated
    },
    {
        "name": "❌ BAD Placeholder",
        "source": "Hello {customer_name}!",
        "target": "你好{顾客姓名}！",  # Wrong: placeholder translated
    }
]

for i, test in enumerate(test_cases, 1):
    print(f"\n   Test {i}: {test['name']}")
    print(f"   📤 Source: {test['source']}")
    print(f"   📥 Target: {test['target']}")
    
    eval_response = requests.post(
        "http://localhost:8000/api/evaluate",
        json={
            "source_text": test["source"],
            "target_text": test["target"], 
            "source_language": "en",
            "target_language": "zh-CN",
            "knowledge_base_id": kb_id
        }
    )
    
    if eval_response.status_code == 200:
        result = eval_response.json()
        score = result.get("score", 0)
        issues = result.get("findings", [])
        
        print(f"   📊 SCORE: {score}/100")
        
        if issues:
            print(f"   🚨 Issues found: {len(issues)}")
            for issue in issues[:2]:  # Show first 2 issues
                print(f"      • {issue.get('description', '')[:80]}...")
        else:
            print(f"   ✅ No issues found!")
    else:
        print(f"   ❌ Evaluation failed: {eval_response.status_code}")

print(f"\n3️⃣ WHAT YOU CAN DO NOW...")
print(f"📖 Interactive API docs: http://localhost:8000/docs")
print(f"🔍 Try different translations")
print(f"📚 Upload your own style guides")
print(f"⚙️  Customize rules and validation logic")

print(f"\n🎉 SYSTEM IS WORKING! You have a complete localization QA system.")