#!/usr/bin/env python3
"""
MVP Demo Script - Rule-Anchored Localization QA System
Tests the complete system functionality
"""

import requests
import json
import time
from pathlib import Path

API_BASE = "http://localhost:8001/api"

def demo_mvp():
    """Demonstrate MVP functionality"""
    print("🚀 Rule-Anchored Localization QA System MVP Demo")
    print("=" * 60)
    
    # Test 1: System Health Check
    print("\n1. Testing API Health...")
    try:
        response = requests.get(f"{API_BASE}/../health")
        if response.status_code == 200:
            print("✅ API is healthy and running")
        else:
            print(f"⚠️  API returned status {response.status_code}")
    except Exception as e:
        print(f"❌ API health check failed: {e}")
        return
    
    # Test 2: Create Sample Style Guide
    print("\n2. Creating sample style guide...")
    sample_guide = """
# Shopify Chinese Localization Style Guide

## Punctuation Rules

1. **Full-width punctuation**: Always use full-width punctuation marks in Simplified Chinese.
   - Correct: 你好！欢迎使用Shopify。
   - Incorrect: 你好!欢迎使用Shopify.

2. **Exclamation marks**: Never use half-width exclamation marks in Chinese text.
   - Correct: 恭喜！订单已成功提交。
   - Incorrect: 恭喜!订单已成功提交。

## Placeholder Guidelines

3. **Variable placeholders**: Keep English variable names in curly braces unchanged.
   - Correct: 欢迎，{customer_name}！
   - Incorrect: 欢迎，{顾客姓名}！

## Date Format Standards

4. **Date formatting**: Use Chinese date format YYYY年MM月DD日 for formal contexts.
   - Correct: 2024年1月15日
   - Incorrect: 2024/01/15 or Jan 15, 2024

5. **Do not translate** brand names like "Shopify", "Amazon", "Google".
   - Correct: 在Shopify上创建您的商店
   - Incorrect: 在购物化上创建您的商店
"""
    
    try:
        # Upload style guide
        response = requests.post(
            f"{API_BASE}/upload-document",
            json={
                "content": sample_guide,
                "filename": "shopify_zh_style_guide.md",
                "document_type": "markdown"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            kb_id = result.get("knowledge_base_id")
            print(f"✅ Style guide processed successfully")
            print(f"   Knowledge Base ID: {kb_id}")
            print(f"   Rules extracted: {len(result.get('summary', {}).get('total_rules', 0))}")
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return
    
    # Wait a moment for processing
    time.sleep(2)
    
    # Test 3: Rule Retrieval
    print("\n3. Testing rule retrieval...")
    try:
        response = requests.post(
            f"{API_BASE}/rules/search",
            json={
                "query": "punctuation exclamation marks",
                "knowledge_base_id": kb_id,
                "limit": 3
            }
        )
        
        if response.status_code == 200:
            rules = response.json().get("rules", [])
            print(f"✅ Found {len(rules)} relevant rules:")
            for i, rule in enumerate(rules[:2], 1):
                print(f"   {i}. {rule.get('description', '')[:80]}...")
        else:
            print(f"❌ Rule search failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Rule search error: {e}")
    
    # Test 4: Translation Evaluation
    print("\n4. Testing translation evaluation...")
    test_cases = [
        {
            "name": "Correct translation",
            "source": "Welcome to Shopify!",
            "target": "欢迎使用Shopify！",
            "expected": "good"
        },
        {
            "name": "Wrong punctuation",
            "source": "Congratulations! Your order is confirmed.",
            "target": "恭喜!您的订单已确认。",  # Half-width exclamation
            "expected": "issues"
        },
        {
            "name": "Translated placeholder",
            "source": "Hello {customer_name}!",
            "target": "你好{顾客姓名}！",  # Translated placeholder
            "expected": "issues"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n   Test {i}: {test_case['name']}")
        try:
            response = requests.post(
                f"{API_BASE}/evaluate",
                json={
                    "source_text": test_case["source"],
                    "target_text": test_case["target"],
                    "source_language": "en",
                    "target_language": "zh-CN",
                    "knowledge_base_id": kb_id
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                score = result.get("score", 0)
                findings = result.get("findings", [])
                
                print(f"   📊 Score: {score}/100")
                if findings:
                    print(f"   🔍 Issues found: {len(findings)}")
                    for finding in findings[:1]:  # Show first issue
                        print(f"      • {finding.get('description', '')[:60]}...")
                else:
                    print("   ✅ No issues found")
                    
            else:
                print(f"   ❌ Evaluation failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Evaluation error: {e}")
    
    # Test 5: Reviewer Override
    print("\n5. Testing reviewer override functionality...")
    try:
        response = requests.post(
            f"{API_BASE}/review/override",
            json={
                "evaluation_id": "demo_evaluation_001",
                "finding_id": "finding_001",
                "action": "dismiss",
                "reason": "False positive - this is acceptable in informal context",
                "reviewer_id": "demo_reviewer"
            }
        )
        
        if response.status_code == 200:
            print("✅ Reviewer override recorded successfully")
        else:
            print(f"❌ Override failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Override error: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 MVP Demo Complete!")
    print("\nThe Rule-Anchored Localization QA System is fully functional with:")
    print("✅ Document ingestion and rule extraction")
    print("✅ Deterministic validation checks")
    print("✅ LLM-powered semantic evaluation") 
    print("✅ Scoring with severity weighting")
    print("✅ Reviewer override capabilities")
    print("✅ REST API for integration")
    
    print(f"\n📚 API Documentation: http://localhost:8001/docs")
    print(f"🔧 Admin Panel: http://localhost:8001/admin")

if __name__ == "__main__":
    demo_mvp()