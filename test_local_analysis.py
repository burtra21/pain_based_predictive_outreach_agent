#!/usr/bin/env python3
"""
Test local analysis to debug signal detection
"""

import sys
import os
sys.path.append('src')

from collectors.company_analyzer import CompanyAnalyzer
from clay_client import ClayClient
from config.settings import config
import traceback

def test_analysis():
    print("🔍 Testing local company analysis...")
    
    # Initialize components
    clay_client = ClayClient(api_key="test", workspace="test")
    analyzer = CompanyAnalyzer(clay_client)
    
    # Test company data
    test_company = {
        "company_name": "Target Corporation",
        "domain": "target.com",
        "industry": "Retail",
        "employee_count": 500000,
        "employeeCount": 500000,
        "linkedin_url": "https://linkedin.com/company/target"
    }
    
    print(f"Testing with: {test_company['company_name']} ({test_company['domain']})")
    print(f"Analysis methods available: {analyzer.analysis_methods}")
    
    # Test individual methods
    print("\n📊 Testing individual analysis methods...")
    
    try:
        # Test HIBP check
        print("Testing HIBP breach check...")
        hibp_signals = analyzer.check_hibp_breaches(test_company)
        print(f"HIBP signals found: {len(hibp_signals)}")
        
        # Test SERPAPI breach check
        print("Testing SERPAPI breach check...")
        serpapi_signals = analyzer.check_breach_mentions_serpapi(test_company)
        print(f"SERPAPI signals found: {len(serpapi_signals)}")
        
        # Test GitHub exposure check
        print("Testing GitHub exposure check...")
        github_signals = analyzer.check_github_exposures(test_company)
        print(f"GitHub signals found: {len(github_signals)}")
        
        # Test Shodan exposure check
        print("Testing Shodan exposure check...")
        if analyzer.shodan_monitor:
            shodan_signals = analyzer.check_shodan_exposures(test_company)
            print(f"Shodan signals found: {len(shodan_signals)}")
        else:
            print("Shodan monitor not initialized (missing API key)")
        
        # Test full company analysis
        print("\n🚀 Testing full company analysis...")
        all_signals = analyzer.analyze_single_company(test_company)
        print(f"Total signals found: {len(all_signals)}")
        
        if all_signals:
            for i, signal in enumerate(all_signals):
                print(f"Signal {i+1}: {signal.get('signal_type', 'unknown')} (strength: {signal.get('signal_strength', 0)})")
        else:
            print("❌ No signals found - checking individual methods for errors")
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_analysis()
