#!/usr/bin/env python3
"""
Test script for BTA collectors
Tests both proactive and reactive data collection
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from clay_client import ClayClient
from collectors.breach_collector import BreachCollector
from collectors.insurance_intel import InsuranceIntelCollector
from collectors.company_analyzer import CompanyAnalyzer
from config.settings import config

def test_clay_connection():
    """Test Clay API connection"""
    print("🔗 Testing Clay API connection...")
    
    try:
        client = ClayClient(config.CLAY_API_KEY, config.CLAY_WORKSPACE)
        
        # Test basic API call
        result = client.get_table('company_universe')
        print(f"✅ Clay connection successful")
        print(f"   API Key: {config.CLAY_API_KEY[:10]}...")
        print(f"   Webhook URL: {config.CLAY_WEBHOOK_URL[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ Clay connection failed: {e}")
        return False

def test_breach_collector():
    """Test breach collector"""
    print("\n🔍 Testing Breach Collector...")
    
    try:
        client = ClayClient(config.CLAY_API_KEY, config.CLAY_WORKSPACE)
        collector = BreachCollector(client)
        
        # Run collection
        collector.run_collection()
        print("✅ Breach collector test completed")
        return True
        
    except Exception as e:
        print(f"❌ Breach collector failed: {e}")
        return False

def test_insurance_intel():
    """Test insurance intelligence collector"""
    print("\n🏢 Testing Insurance Intelligence Collector...")
    
    try:
        client = ClayClient(config.CLAY_API_KEY, config.CLAY_WORKSPACE)
        collector = InsuranceIntelCollector(client)
        
        # Run collection
        collector.run_collection()
        print("✅ Insurance intelligence test completed")
        return True
        
    except Exception as e:
        print(f"❌ Insurance intelligence failed: {e}")
        return False

def test_company_analyzer():
    """Test company analyzer"""
    print("\n📊 Testing Company Analyzer...")
    
    try:
        client = ClayClient(config.CLAY_API_KEY, config.CLAY_WORKSPACE)
        analyzer = CompanyAnalyzer(client)
        
        # Run analysis on small batch
        analyzer.run_analysis(batch_size=5)
        print("✅ Company analyzer test completed")
        return True
        
    except Exception as e:
        print(f"❌ Company analyzer failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 BTA Collector Test Suite")
    print("=" * 50)
    
    tests = [
        ("Clay Connection", test_clay_connection),
        ("Breach Collector", test_breach_collector),
        ("Insurance Intelligence", test_insurance_intel),
        ("Company Analyzer", test_company_analyzer)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your collectors are ready.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
