"""
Intelligent Data Flow Optimizer
Determines the optimal data source for each signal type
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import requests
import json

class DataFlowOptimizer:
    """Optimizes data collection based on signal type and company context"""
    
    def __init__(self, clay_client):
        self.clay_client = clay_client
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BTA-Optimizer/1.0'
        })
        
        # Signal priority matrix - higher = more valuable
        self.signal_priorities = {
            'active_ransomware': 100,      # Maximum urgency
            'breach_notification': 95,     # Very high
            'post_breach': 90,             # High
            'insurance_coverage_issue': 85, # High
            'skills_gap_critical': 80,     # High
            'executive_vacancy_critical': 75, # Medium-high
            'security_tech_gaps': 70,      # Medium-high
            'compliance_vulnerability': 65, # Medium
            'high_insurance_risk': 60,     # Medium
            'breach_mention_detected': 55, # Medium-low
            'security_job_postings': 50,   # Low-medium
            'dark_web_mention': 45         # Low-medium
        }
        
        # Data source efficiency matrix
        self.source_efficiency = {
            'breach_collector': {
                'signals_per_hour': 50,    # Very efficient
                'accuracy': 0.95,         # Very accurate
                'cost': 'free',
                'coverage': 'public_breaches'
            },
            'insurance_intel': {
                'signals_per_hour': 20,    # Medium efficiency
                'accuracy': 0.85,         # Good accuracy
                'cost': 'free',
                'coverage': 'insurance_issues'
            },
            'company_analyzer': {
                'signals_per_hour': 100,   # Very efficient (batch processing)
                'accuracy': 0.75,         # Medium accuracy
                'cost': 'free',
                'coverage': 'existing_companies'
            },
            'builtwith_api': {
                'signals_per_hour': 200,   # Very efficient
                'accuracy': 0.90,         # Very accurate
                'cost': '$99/month',
                'coverage': 'tech_stack'
            },
            'wappalyzer_api': {
                'signals_per_hour': 150,   # Efficient
                'accuracy': 0.85,         # Good accuracy
                'cost': '$29/month',
                'coverage': 'tech_stack'
            }
        }
    
    def optimize_data_collection_strategy(self) -> Dict:
        """Determine optimal data collection strategy"""
        
        strategy = {
            'proactive_collection': {
                'breach_collector': {
                    'priority': 'high',
                    'frequency': 'daily',
                    'reason': 'High-value breach signals, very efficient'
                },
                'insurance_intel': {
                    'priority': 'medium',
                    'frequency': 'daily',
                    'reason': 'Good insurance signals, moderate efficiency'
                },
                'job_collector': {
                    'priority': 'medium',
                    'frequency': 'daily',
                    'reason': 'Skills gap signals, good efficiency'
                },
                'dark_web_monitor': {
                    'priority': 'low',
                    'frequency': 'daily',
                    'reason': 'Lower-value signals, moderate efficiency'
                }
            },
            'reactive_analysis': {
                'company_analyzer': {
                    'priority': 'high',
                    'frequency': 'continuous',
                    'reason': 'Analyzes existing 50K+ companies efficiently'
                },
                'builtwith_integration': {
                    'priority': 'high',
                    'frequency': 'on_demand',
                    'reason': 'High-value tech stack signals, very efficient'
                }
            },
            'hybrid_approach': {
                'tech_stack_signals': {
                    'primary_source': 'builtwith_api',
                    'fallback_source': 'company_analyzer',
                    'reason': 'BuiltWith more accurate, analyzer as backup'
                },
                'breach_signals': {
                    'primary_source': 'breach_collector',
                    'fallback_source': 'company_analyzer',
                    'reason': 'Breach collector finds new breaches, analyzer finds mentions'
                },
                'insurance_signals': {
                    'primary_source': 'insurance_intel',
                    'fallback_source': 'company_analyzer',
                    'reason': 'Insurance intel finds specific issues, analyzer finds general risk'
                }
            }
        }
        
        return strategy
    
    def get_optimal_signal_sources(self, signal_type: str) -> List[str]:
        """Get optimal data sources for a specific signal type"""
        
        signal_source_mapping = {
            'active_ransomware': ['dark_web_monitor', 'company_analyzer'],
            'breach_notification': ['breach_collector', 'company_analyzer'],
            'post_breach': ['breach_collector', 'company_analyzer'],
            'insurance_coverage_issue': ['insurance_intel', 'company_analyzer'],
            'skills_gap_critical': ['job_collector', 'company_analyzer'],
            'executive_vacancy_critical': ['job_collector', 'company_analyzer'],
            'security_tech_gaps': ['builtwith_api', 'company_analyzer'],
            'compliance_vulnerability': ['company_analyzer'],
            'high_insurance_risk': ['insurance_intel', 'company_analyzer'],
            'breach_mention_detected': ['company_analyzer'],
            'security_job_postings': ['job_collector', 'company_analyzer'],
            'dark_web_mention': ['dark_web_monitor', 'company_analyzer']
        }
        
        return signal_source_mapping.get(signal_type, ['company_analyzer'])
    
    def calculate_signal_value(self, signal: Dict) -> float:
        """Calculate the value of a signal based on multiple factors"""
        
        signal_type = signal.get('signal_type', '')
        signal_strength = signal.get('signal_strength', 0)
        
        # Base priority score
        base_priority = self.signal_priorities.get(signal_type, 30)
        
        # Adjust by signal strength
        adjusted_priority = base_priority * signal_strength
        
        # Adjust by recency (newer = more valuable)
        signal_date = signal.get('signal_date', '')
        if signal_date:
            try:
                signal_datetime = datetime.fromisoformat(signal_date.replace('Z', '+00:00'))
                days_old = (datetime.utcnow() - signal_datetime).days
                
                # Reduce value for older signals
                if days_old > 30:
                    adjusted_priority *= 0.8
                elif days_old > 7:
                    adjusted_priority *= 0.9
                    
            except:
                pass
        
        # Adjust by company size (larger companies = more valuable)
        company_size = signal.get('raw_data', {}).get('company_size', 'smb')
        if company_size == 'enterprise':
            adjusted_priority *= 1.2
        elif company_size == 'mid_market':
            adjusted_priority *= 1.1
        
        return adjusted_priority
    
    def optimize_tech_stack_collection(self) -> Dict:
        """Determine optimal approach for tech stack signals"""
        
        # Check if we have BuiltWith data in Clay
        try:
            # Query a sample company to see if BuiltWith data exists
            sample_companies = self.clay_client.query_table(
                'company_universe',
                {'tech_stack_analyzed': True}
            )
            
            if sample_companies:
                return {
                    'approach': 'use_clay_builtwith',
                    'reason': 'BuiltWith data already exists in Clay',
                    'action': 'Read from Clay, analyze for security gaps',
                    'efficiency': 'high'
                }
            else:
                return {
                    'approach': 'api_collection',
                    'reason': 'No BuiltWith data in Clay yet',
                    'action': 'Use BuiltWith API for tech stack analysis',
                    'efficiency': 'medium'
                }
                
        except Exception as e:
            return {
                'approach': 'api_collection',
                'reason': f'Error checking Clay data: {e}',
                'action': 'Use BuiltWith API for tech stack analysis',
                'efficiency': 'medium'
            }
    
    def get_collection_priorities(self) -> List[Dict]:
        """Get prioritized list of collection activities"""
        
        priorities = [
            {
                'collector': 'breach_collector',
                'priority': 1,
                'reason': 'Highest value signals, very efficient',
                'expected_signals_per_run': '10-50',
                'signal_types': ['breach_notification', 'post_breach']
            },
            {
                'collector': 'company_analyzer',
                'priority': 2,
                'reason': 'Analyzes existing 50K+ companies efficiently',
                'expected_signals_per_run': '20-40',
                'signal_types': ['breach_mention_detected', 'security_job_postings', 'tech_gaps']
            },
            {
                'collector': 'insurance_intel',
                'priority': 3,
                'reason': 'Good insurance signals, moderate efficiency',
                'expected_signals_per_run': '10-28',
                'signal_types': ['insurance_coverage_issue', 'high_insurance_risk']
            },
            {
                'collector': 'job_collector',
                'priority': 4,
                'reason': 'Skills gap signals, good efficiency',
                'expected_signals_per_run': '30-80',
                'signal_types': ['skills_gap_critical', 'executive_vacancy_critical']
            },
            {
                'collector': 'dark_web_monitor',
                'priority': 5,
                'reason': 'Lower value but unique signals',
                'expected_signals_per_run': '5-20',
                'signal_types': ['active_ransomware', 'dark_web_mention']
            }
        ]
        
        return priorities
    
    def optimize_for_maximum_outreach(self) -> Dict:
        """Optimize for maximum outreach volume and quality"""
        
        optimization_strategy = {
            'volume_optimization': {
                'company_analyzer': {
                    'batch_size': 500,  # Larger batches for efficiency
                    'frequency': 'every_4_hours',
                    'reason': 'Process more companies faster'
                },
                'breach_collector': {
                    'frequency': 'every_6_hours',
                    'reason': 'Catch breaches faster'
                },
                'insurance_intel': {
                    'frequency': 'daily',
                    'reason': 'Insurance signals change slowly'
                }
            },
            'quality_optimization': {
                'signal_filtering': {
                    'min_signal_strength': 0.6,
                    'reason': 'Focus on high-confidence signals'
                },
                'company_prioritization': {
                    'enterprise_first': True,
                    'reason': 'Larger companies = bigger deals'
                },
                'recency_bonus': {
                    'recent_signals_multiplier': 1.2,
                    'reason': 'Fresh signals are more valuable'
                }
            },
            'edp_optimization': {
                'primary_edps': [
                    'active_ransomware',      # Highest urgency
                    'breach_notification',   # Very high urgency
                    'insurance_coverage_issue', # High urgency
                    'skills_gap_critical',   # High urgency
                    'security_tech_gaps'     # Medium-high urgency
                ],
                'segmentation_strategy': {
                    'post_breach_survivor': 'immediate_outreach',
                    'insurance_pressured': 'high_priority',
                    'skills_gap_sufferer': 'high_priority',
                    'resource_constrained': 'medium_priority',
                    'overwhelmed_generalist': 'nurture_sequence'
                }
            }
        }
        
        return optimization_strategy
