import pytest
from datetime import datetime
import json

class TestBTAIntegration:
    def test_clay_connection(self):
        """Test Clay API connection"""
        from clay_client import ClayClient
        from config.settings import config
        
        client = ClayClient(config.CLAY_API_KEY, config.CLAY_WORKSPACE)
        
        # Test table access
        result = client.get_table('company_universe')
        assert result is not None
    
    def test_breach_collection(self):
        """Test breach data collection"""
        from collectors.breach_collector import BreachCollector
        
        collector = BreachCollector(None)  # Mock Clay client
        breaches = collector.collect_ca_breaches()
        
        assert isinstance(breaches, list)
        if breaches:
            assert 'company_name' in breaches[0]
    
    def test_scoring_logic(self):
        """Test EDP scoring"""
        from scoring.edp_scorer import EDPScorer
        
        scorer = EDPScorer(None)  # Mock Clay client
        
        # Test with mock signals
        signals = [
            {
                'signal_type': 'post_breach',
                'signal_date': datetime.now().isoformat(),
                'signal_strength': 0.9
            }
        ]
        
        score = scorer.calculate_dwell_score('test.com', signals)
        assert 0 <= score <= 1.0
    
    def test_campaign_generation(self):
        """Test campaign personalization"""
        from campaigns.campaign_generator import CampaignGenerator
        
        gen = CampaignGenerator(None)  # Mock Clay client
        
        company = {'company_name': 'Test Corp', 'domain': 'test.com'}
        contact = {'name': 'John Doe', 'email': 'john@test.com'}
        score_data = {'primary_edp': 'dwell_time', 'pain_score': 85}
        
        template = gen.templates['dwell_time']
        personalized = gen.personalize_message(
            template, company, contact, score_data
        )
        
        assert '[COMPANY]' not in personalized['body']
        assert 'Test Corp' in personalized['body']