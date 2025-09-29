from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import numpy as np

class EDPScorer:
    def __init__(self, clay_client):
        self.clay_client = clay_client
        self.weights = {
            'dwell_time': 0.35,
            'skills_gap': 0.25,
            'after_hours': 0.15,
            'insurance': 0.15,
            'breach_cost': 0.10
        }
    
    def calculate_company_score(self, domain: str) -> Dict:
        """Calculate comprehensive pain score for a company"""
        # Fetch all signals for company
        signals = self.clay_client.query_table(
            'pain_signals',
            {'domain': domain}
        )
        
        # Calculate individual EDP scores
        scores = {
            'dwell_time': self.calculate_dwell_score(domain, signals),
            'skills_gap': self.calculate_skills_gap_score(domain, signals),
            'after_hours': self.calculate_after_hours_score(domain, signals),
            'insurance': self.calculate_insurance_score(domain, signals),
            'breach_cost': self.calculate_breach_cost_score(domain, signals)
        }
        
        # Calculate weighted total
        total_score = sum(scores[k] * self.weights[k] for k in scores)
        
        # Determine primary EDP
        primary_edp = max(scores, key=scores.get)
        
        # Determine segment
        segment = self.assign_segment(signals, scores)
        
        return {
            'domain': domain,
            'pain_score': total_score * 100,  # Convert to 0-100 scale
            'individual_scores': scores,
            'primary_edp': primary_edp,
            'segment': segment,
            'recommendation': self.get_recommendation(total_score * 100, segment),
            'timestamp': datetime.now().isoformat()
        }
    
    def calculate_dwell_score(self, domain: str, signals: List[Dict]) -> float:
        """Calculate 277-day dwell time risk score"""
        score = 0.0
        
        # Check for breach history
        breach_signals = [s for s in signals if 'breach' in s.get('signal_type', '')]
        if breach_signals:
            # Recent breach = high dwell risk
            most_recent = max(breach_signals, key=lambda x: x['signal_date'])
            days_since = (datetime.now() - datetime.fromisoformat(most_recent['signal_date'])).days
            
            if days_since < 30:
                score += 0.9
            elif days_since < 90:
                score += 0.7
            elif days_since < 180:
                score += 0.5
            else:
                score += 0.3
        
        # Check for security tool gaps
        tech_stack = self.get_tech_stack(domain)
        if not tech_stack.get('has_mdr'):
            score += 0.3
        if not tech_stack.get('has_siem'):
            score += 0.2
        if not tech_stack.get('has_edr'):
            score += 0.2
        
        # Check for 24/7 coverage
        vacancy_signals = [s for s in signals if 'vacancy' in s.get('signal_type', '')]
        if vacancy_signals:
            score += 0.2
        
        return min(score, 1.0)
    
    def calculate_skills_gap_score(self, domain: str, signals: List[Dict]) -> float:
        """Calculate $1.76M skills gap tax score"""
        score = 0.0
        
        # Check for long-term vacancies
        vacancy_signals = [s for s in signals if 'vacancy' in s.get('signal_type', '')]
        
        for vacancy in vacancy_signals:
            days_open = vacancy.get('raw_data', {}).get('days_open', 0)
            
            if days_open > 90:
                score += 0.4
            elif days_open > 60:
                score += 0.3
            elif days_open > 30:
                score += 0.2
            
            # Executive positions score higher
            if 'executive' in vacancy.get('signal_type', ''):
                score += 0.2
        
        return min(score, 1.0)
    
    def calculate_after_hours_score(self, domain: str, signals: List[Dict]) -> float:
        """Calculate 76% after-hours vulnerability score"""
        score = 0.5  # Base assumption: most companies vulnerable
        
        # Check if they have 24/7 coverage indicators
        tech_stack = self.get_tech_stack(domain)
        
        if tech_stack.get('has_mdr'):
            score -= 0.4
        if tech_stack.get('has_mssp'):
            score -= 0.3
        
        # Increase if in high-risk industry
        company = self.get_company_info(domain)
        if company.get('industry') in ['healthcare', 'finance', 'critical_infrastructure']:
            score += 0.2
        
        return max(min(score, 1.0), 0.0)
    
    def calculate_insurance_score(self, domain: str, signals: List[Dict]) -> float:
        """Calculate cyber insurance pressure score"""
        score = 0.0
        
        # Check for breach history (affects premiums)
        breach_signals = [s for s in signals if 'breach' in s.get('signal_type', '')]
        if breach_signals:
            score += 0.4
        
        # Industry-specific insurance requirements
        company = self.get_company_info(domain)
        if company.get('industry') in ['healthcare', 'finance']:
            score += 0.3
        
        # Check for compliance issues
        compliance_signals = [s for s in signals if 'compliance' in s.get('signal_type', '')]
        if compliance_signals:
            score += 0.3
        
        return min(score, 1.0)
    
    def calculate_breach_cost_score(self, domain: str, signals: List[Dict]) -> float:
        """Calculate potential breach cost impact"""
        company = self.get_company_info(domain)
        
        # Base score by company size
        employees = company.get('employee_count', 100)
        if employees > 5000:
            base_score = 0.8
        elif employees > 1000:
            base_score = 0.6
        elif employees > 500:
            base_score = 0.4
        else:
            base_score = 0.3
        
        # Adjust by industry
        industry_multipliers = {
            'healthcare': 1.5,
            'finance': 1.3,
            'retail': 1.2,
            'manufacturing': 1.1,
            'technology': 1.1
        }
        
        multiplier = industry_multipliers.get(company.get('industry', ''), 1.0)
        
        return min(base_score * multiplier, 1.0)
    
    def assign_segment(self, signals: List[Dict], scores: Dict) -> str:
        """Assign company to primary segment"""
        # Priority order based on conversion rates
        
        # 1. Post-breach survivors (highest priority)
        breach_signals = [s for s in signals if 'breach' in s.get('signal_type', '')]
        if breach_signals:
            most_recent = max(breach_signals, key=lambda x: x['signal_date'])
            days_since = (datetime.now() - datetime.fromisoformat(most_recent['signal_date'])).days
            if days_since < 90:
                return 'post_breach_survivor'
        
        # 2. Skills gap sufferers
        if scores['skills_gap'] > 0.7:
            return 'skills_gap_sufferer'
        
        # 3. Insurance pressured
        if scores['insurance'] > 0.7:
            return 'insurance_pressured'
        
        # 4. Resource constrained (high dwell risk)
        if scores['dwell_time'] > 0.6:
            return 'resource_constrained'
        
        # 5. Overwhelmed generalist (default for SMBs)
        company = self.get_company_info(signals[0]['domain'] if signals else '')
        if company.get('employee_count', 0) < 500:
            return 'overwhelmed_generalist'
        
        return 'general_prospect'
    
    def get_recommendation(self, score: float, segment: str) -> str:
        """Get outreach recommendation based on score and segment"""
        if score >= 90:
            return 'immediate_outreach_priority'
        elif score >= 75:
            return 'high_priority_outreach'
        elif score >= 60:
            return 'medium_priority_nurture'
        elif score >= 45:
            return 'low_priority_monitor'
        else:
            return 'not_qualified'
    
    def get_company_info(self, domain: str) -> Dict:
        """Fetch company information from Clay"""
        companies = self.clay_client.query_table(
            'company_universe',
            {'domain': domain}
        )
        return companies[0] if companies else {}
    
    def get_tech_stack(self, domain: str) -> Dict:
        """Get technology stack information"""
        # This would integrate with Wappalyzer/BuiltWith data
        # Placeholder for now
        return {
            'has_mdr': False,
            'has_siem': False,
            'has_edr': False,
            'has_mssp': False
        }