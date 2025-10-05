#!/usr/bin/env python3
"""
Test script to verify that quality checks are working correctly.
This tests the new two-phase evaluation system.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.evaluation_engine import EvaluationEngine

async def test_quality_checks():
    """Test that quality checks catch obvious translation errors"""
    
    engine = EvaluationEngine()
    
    # Test cases with deliberately bad translations
    test_cases = [
        {
            "name": "Script Mixing (Pinyin + Chinese)",
            "source": "What is your name?",
            "target": "您叫什么mingzi？",
            "locale": "zh-CN",
            "expected_issues": ["script_mixing"],
            "should_fail": True
        },
        {
            "name": "Wrong Meaning + Colloquial",
            "source": "What is your name and how old are you?",
            "target": "你叫啥名字和你大了？",
            "locale": "zh-CN",
            "expected_issues": ["accuracy_error", "professionalism_error"],
            "should_fail": True
        },
        {
            "name": "Good Translation (Control)",
            "source": "What is your name?",
            "target": "你叫什么名字？",
            "locale": "zh-CN",
            "expected_issues": [],
            "should_fail": False
        }
    ]
    
    print("=" * 80)
    print("TESTING NEW TWO-PHASE QUALITY EVALUATION SYSTEM")
    print("=" * 80)
    print()
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"Test Case {i}: {test['name']}")
        print(f"{'=' * 80}")
        print(f"Source: {test['source']}")
        print(f"Target: {test['target']}")
        print(f"Expected: {'SHOULD CATCH ERRORS' if test['should_fail'] else 'SHOULD PASS'}")
        print()
        
        try:
            result = await engine.evaluate(
                source_text=test['source'],
                target_text=test['target'],
                locale=test['locale']
            )
            
            print(f"\n📊 RESULTS:")
            print(f"   Final Score: {result.final_score}/100")
            print(f"   Issues Found: {len(result.findings)}")
            
            if result.findings:
                print(f"\n   ⚠️  Issues Detected:")
                for finding in result.findings:
                    print(f"      - {finding.rule_id}")
                    print(f"        Severity: {finding.severity.value}")
                    print(f"        Penalty: {finding.penalty}")
                    print(f"        Text: '{finding.highlighted_text}'")
                    print(f"        Reason: {finding.justification[:100]}...")
                    print()
            
            # Verify results
            if test['should_fail']:
                if result.final_score >= 95:
                    print(f"\n   ❌ TEST FAILED: Score too high ({result.final_score}), should catch errors!")
                    print(f"      Expected issues: {test['expected_issues']}")
                else:
                    print(f"\n   ✅ TEST PASSED: Errors correctly detected!")
            else:
                if result.final_score >= 90:
                    print(f"\n   ✅ TEST PASSED: Good translation recognized!")
                else:
                    print(f"\n   ⚠️  WARNING: Score lower than expected ({result.final_score})")
            
            print(f"\n   Score Breakdown by Category:")
            for macro_class, breakdown in result.by_macro.items():
                if breakdown.count > 0:
                    print(f"      {macro_class}: -{breakdown.penalty} points ({breakdown.count} issues)")
        
        except Exception as e:
            print(f"\n   ❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'=' * 80}")
    print("TESTING COMPLETE")
    print(f"{'=' * 80}\n")

if __name__ == "__main__":
    print("\n🔍 Starting Quality Check Tests...\n")
    print("NOTE: Make sure LM Studio is running with both:")
    print("  1. Chat model (for evaluation)")
    print("  2. Embedding model (for rule retrieval)")
    print()
    
    try:
        asyncio.run(test_quality_checks())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

