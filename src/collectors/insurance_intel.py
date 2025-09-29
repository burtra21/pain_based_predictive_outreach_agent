import requests
from datetime import datetime, timedelta
from typing import List, Dict
import json
import re
import time

class InsuranceIntelCollector:
    def __init__(self, clay_client):
        self.clay_client = clay_client
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BTA-InsuranceIntel/1.0'
        })
        
        # Major cyber insurance providers
        self.insurers = [
            'Chubb', 'AIG', 'Travelers', 'Hartford',
            'Zurich', 'Liberty Mutual', 'CNA', 'Beazley',
            'Coalition', 'At-Bay', 'Cowbell Cyber'
        ]
        
    def collect_insurance_signals(self) -> List[Dict]:
        """Collect cyber insurance market signals"""
        signals = []
        
        print("Collecting cyber insurance intelligence...")
        
        # Check insurance requirement changes
        signals.extend(self.scan_insurance_requirements())
        
        # Check companies approaching renewal
        signals.extend(self.identify_renewal_opportunities())
        
        # Analyze existing companies for insurance risks
        signals.extend(self.analyze_existing_companies_for_risks())
        
        return signals
    
    def scan_insurance_requirements(self) -> List[Dict]:
        """Scan for companies with specific insurance gaps or denied coverage"""
        signals = []
        
        try:
            # Enhanced approach: Use multiple data sources
            print("Scanning for insurance requirement changes...")
            
            # Method 1: SEC Filings for insurance-related disclosures
            sec_signals = self.scan_sec_insurance_disclosures()
            signals.extend(sec_signals)
            
            # Method 2: Industry news with better targeting
            news_signals = self.scan_insurance_news_enhanced()
            signals.extend(news_signals)
            
            # Method 3: Regulatory filings and state insurance databases
            regulatory_signals = self.scan_regulatory_insurance_data()
            signals.extend(regulatory_signals)
            
        except Exception as e:
            print(f"Error in insurance requirements scan: {e}")
        
        return signals[:10]  # Increased limit for better coverage
    
    def scan_sec_insurance_disclosures(self) -> List[Dict]:
        """Scan SEC filings for cyber insurance disclosures"""
        signals = []
        
        try:
            # Search SEC EDGAR for cyber insurance mentions
            search_terms = [
                "cyber insurance",
                "cyber liability",
                "data breach insurance",
                "cybersecurity insurance"
            ]
            
            for term in search_terms:
                try:
                    # Use SEC EDGAR search API
                    response = self.session.get(
                        'https://www.sec.gov/cgi-bin/browse-edgar',
                        params={
                            'action': 'getcompany',
                            'CIK': '',  # We'll search by text
                            'type': '10-K',  # Annual reports
                            'dateb': '',  # Recent filings
                            'owner': 'exclude',
                            'count': '100',
                            'search_text': term
                        },
                        timeout=15
                    )
                    
                    if response.status_code == 200:
                        companies = self.extract_sec_insurance_companies(response.text, term)
                        signals.extend(companies)
                    
                    time.sleep(2)  # Respectful delay
                    
                except Exception as e:
                    print(f"Error searching SEC for '{term}': {e}")
                    continue
                    
        except Exception as e:
            print(f"Error in SEC insurance scan: {e}")
        
        return signals
    
    def scan_insurance_news_enhanced(self) -> List[Dict]:
        """Enhanced news scanning with better targeting"""
        signals = []
        
        try:
            # More specific search terms that are likely to yield results
            targeted_terms = [
                "cyber insurance denied",
                "cyber insurance canceled",
                "cyber insurance premium increase",
                "cyber insurance claim",
                "cyber insurance coverage gap"
            ]
            
            for term in targeted_terms:
                try:
                    # Use multiple news sources
                    sources = [
                        'https://news.google.com/rss/search',
                        'https://feeds.finance.yahoo.com/rss/2.0/headline'
                    ]
                    
                    for source in sources:
                        response = self.session.get(
                            source,
                            params={
                                'q': f'"{term}"',
                                'hl': 'en',
                                'gl': 'US',
                                'ceid': 'US:en'
                            },
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            companies = self.extract_companies_with_insurance_issues(response.text, term)
                            signals.extend(companies)
                        
                        time.sleep(2)
                    
                except Exception as e:
                    print(f"Error searching news for '{term}': {e}")
                    continue
                    
        except Exception as e:
            print(f"Error in enhanced news scan: {e}")
        
        return signals
    
    def scan_regulatory_insurance_data(self) -> List[Dict]:
        """Scan state insurance regulatory data"""
        signals = []
        
        try:
            # State insurance department websites often have public data
            state_sites = [
                'https://www.insurance.ca.gov',
                'https://www.dfs.ny.gov',
                'https://www.tdi.texas.gov'
            ]
            
            for site in state_sites:
                try:
                    # Look for cyber insurance bulletins or notices
                    response = self.session.get(f"{site}/bulletin", timeout=10)
                    
                    if response.status_code == 200:
                        companies = self.extract_regulatory_insurance_companies(response.text, site)
                        signals.extend(companies)
                    
                    time.sleep(3)
                    
                except Exception as e:
                    print(f"Error scanning {site}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error in regulatory scan: {e}")
        
        return signals
    
    def extract_sec_insurance_companies(self, html_content: str, search_term: str) -> List[Dict]:
        """Extract companies from SEC filings mentioning insurance"""
        signals = []
        
        try:
            # Look for company names in SEC filings
            company_patterns = [
                r'([A-Z][a-zA-Z\s]+(?:Inc|Corp|LLC|Ltd|Co\.?))[\s\w]*(?:cyber insurance|cyber liability)',
                r'(?:cyber insurance|cyber liability)[\s\w]*([A-Z][a-zA-Z\s]+(?:Inc|Corp|LLC|Ltd|Co\.?))'
            ]
            
            for pattern in company_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches[:3]:  # Limit to top 3 per pattern
                    if len(match.strip()) > 5 and len(match.strip()) < 50:
                        signal = {
                            'company_name': match.strip(),
                            'domain': self.estimate_domain(match.strip()),
                            'signal_type': 'sec_insurance_disclosure',
                            'signal_date': datetime.utcnow().isoformat(),
                            'signal_strength': 0.8,  # High confidence from SEC filings
                            'raw_data': {
                                'source': 'sec_edgar',
                                'search_term': search_term,
                                'disclosure_type': 'annual_report',
                                'confidence': 'high'
                            },
                            'source': 'sec_filings'
                        }
                        signals.append(signal)
                        print(f"Found SEC insurance disclosure: {match.strip()}")
                        
        except Exception as e:
            print(f"Error extracting SEC companies: {e}")
        
        return signals
    
    def extract_regulatory_insurance_companies(self, html_content: str, site: str) -> List[Dict]:
        """Extract companies from regulatory insurance data"""
        signals = []
        
        try:
            # Look for company mentions in regulatory bulletins
            company_patterns = [
                r'([A-Z][a-zA-Z\s]+(?:Inc|Corp|LLC|Ltd|Co\.?))[\s\w]*(?:cyber|data breach|security)',
                r'(?:cyber|data breach|security)[\s\w]*([A-Z][a-zA-Z\s]+(?:Inc|Corp|LLC|Ltd|Co\.?))'
            ]
            
            for pattern in company_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches[:2]:  # Limit to top 2 per pattern
                    if len(match.strip()) > 5 and len(match.strip()) < 50:
                        signal = {
                            'company_name': match.strip(),
                            'domain': self.estimate_domain(match.strip()),
                            'signal_type': 'regulatory_insurance_notice',
                            'signal_date': datetime.utcnow().isoformat(),
                            'signal_strength': 0.7,  # Medium-high confidence from regulatory data
                            'raw_data': {
                                'source': site,
                                'regulatory_type': 'insurance_bulletin',
                                'confidence': 'medium_high'
                            },
                            'source': 'regulatory_data'
                        }
                        signals.append(signal)
                        print(f"Found regulatory insurance notice: {match.strip()}")
                        
        except Exception as e:
            print(f"Error extracting regulatory companies: {e}")
        
        return signals
    
    def identify_renewal_opportunities(self) -> List[Dict]:
        """Identify companies likely approaching insurance renewal"""
        signals = []
        
        try:
            # Get companies from Clay database
            try:
                companies = self.clay_client.query_table(
                    'company_universe',
                    {'insurance_checked': False}
                )
            except Exception as e:
                print(f"Error querying companies: {e}")
                return signals
            
            if not companies:
                print("No companies need insurance analysis")
                return signals
            
            if not isinstance(companies, list):
                try:
                    companies = list(companies) if companies else []
                except:
                    return signals
            
            # Analyze up to 20 companies per run
            companies = companies[:20]
            print(f"Analyzing {len(companies)} companies for insurance renewal opportunities")
            
            company_updates = []
            
            for company in companies:
                if not isinstance(company, dict):
                    continue
                    
                domain = company.get('domain')
                company_name = company.get('company_name', '')
                
                if not domain or not company_name:
                    continue
                
                # Estimate insurance renewal timing
                renewal_data = self.estimate_renewal_opportunity(company)
                
                if renewal_data and renewal_data.get('signal_strength', 0) > 0.5:
                    signal = {
                        'company_name': company_name,
                        'domain': domain,
                        'signal_type': 'insurance_renewal_opportunity',
                        'signal_date': datetime.utcnow().isoformat(),
                        'signal_strength': renewal_data['signal_strength'],
                        'raw_data': renewal_data,
                        'source': 'insurance_intel'
                    }
                    signals.append(signal)
                
                # Mark as checked
                company_updates.append({
                    'company_name': company_name,
                    'domain': domain,
                    'insurance_checked': True,
                    'last_insurance_check': datetime.utcnow().isoformat()
                })
            
            # Update companies as checked
            if company_updates:
                try:
                    self.clay_client.bulk_upsert('company_universe', company_updates)
                    print(f"Updated {len(company_updates)} companies as insurance-checked")
                except Exception as e:
                    print(f"Error updating insurance check status: {e}")
                    
        except Exception as e:
            print(f"Error in renewal opportunities identification: {e}")
        
        return signals
    
    def estimate_renewal_opportunity(self, company: Dict) -> Dict:
        """Estimate insurance renewal opportunity based on company data"""
        try:
            domain = company.get('domain', '')
            company_name = company.get('company_name', '')
            
            # Start with base opportunity score
            opportunity_score = 0.4
            renewal_factors = []
            
            # Factor 1: Recent breach history (from other collectors)
            if self.has_recent_breach_signals(domain):
                opportunity_score += 0.3
                renewal_factors.append("recent_breach_activity")
            
            # Factor 2: Company size estimation (based on domain patterns)
            if self.estimate_company_size(domain, company_name) == 'enterprise':
                opportunity_score += 0.2
                renewal_factors.append("enterprise_size")
            
            # Factor 3: Industry risk factors
            if self.is_high_risk_industry(company_name):
                opportunity_score += 0.2
                renewal_factors.append("high_risk_industry")
            
            # Factor 4: Seasonality (Q4 is common renewal period)
            current_month = datetime.now().month
            if current_month in [10, 11, 12, 1]:  # Q4/Q1 renewal season
                opportunity_score += 0.1
                renewal_factors.append("renewal_season")
            
            # Cap at 1.0
            opportunity_score = min(opportunity_score, 1.0)
            
            if opportunity_score > 0.5:
                return {
                    'signal_strength': opportunity_score,
                    'renewal_factors': renewal_factors,
                    'estimated_renewal_window': self.estimate_renewal_window(),
                    'recommended_approach': self.get_approach_recommendation(renewal_factors)
                }
            
        except Exception as e:
            print(f"Error estimating renewal opportunity for {company.get('domain', 'unknown')}: {e}")
        
        return None
    
    def has_recent_breach_signals(self, domain: str) -> bool:
        """Check if company has recent breach/threat signals"""
        try:
            signals = self.clay_client.query_table(
                'pain_signals',
                {'domain': domain}
            )
            
            if signals:
                # Check if any signals are recent (within 6 months)
                six_months_ago = datetime.utcnow() - timedelta(days=180)
                for signal in signals:
                    signal_date_str = signal.get('signal_date', '')
                    if signal_date_str:
                        try:
                            signal_date = datetime.fromisoformat(signal_date_str.replace('Z', '+00:00'))
                            if signal_date > six_months_ago:
                                return True
                        except:
                            continue
        except:
            pass
        return False
    
    def estimate_company_size(self, domain: str, company_name: str) -> str:
        """Estimate company size from domain and name patterns"""
        # Simple heuristics for company size
        enterprise_indicators = [
            'corp', 'corporation', 'inc', 'llc', 'ltd', 'group',
            'holdings', 'international', 'global', 'systems'
        ]
        
        name_lower = company_name.lower()
        if any(indicator in name_lower for indicator in enterprise_indicators):
            return 'enterprise'
        
        # Domain patterns
        if len(domain.replace('.com', '')) > 15:  # Longer domains often = larger companies
            return 'enterprise'
        
        return 'smb'
    
    def is_high_risk_industry(self, company_name: str) -> bool:
        """Identify high cyber risk industries"""
        high_risk_keywords = [
            'healthcare', 'medical', 'hospital', 'clinic',
            'financial', 'bank', 'credit', 'insurance',
            'technology', 'tech', 'software', 'data',
            'manufacturing', 'energy', 'utilities',
            'legal', 'law', 'government', 'municipal'
        ]
        
        name_lower = company_name.lower()
        return any(keyword in name_lower for keyword in high_risk_keywords)
    
    def estimate_renewal_window(self) -> str:
        """Estimate likely renewal window"""
        import random
        windows = [
            "Q4 2024", "Q1 2025", "Q2 2025", "Q3 2025"
        ]
        return random.choice(windows)
    
    def get_approach_recommendation(self, factors: List[str]) -> str:
        """Get recommended outreach approach"""
        if 'recent_breach_activity' in factors:
            return "immediate_security_consultation"
        elif 'renewal_season' in factors:
            return "renewal_optimization_review"
        elif 'high_risk_industry' in factors:
            return "industry_specific_risk_assessment"
        else:
            return "general_insurance_review"
    
    def extract_companies_with_insurance_issues(self, rss_text: str, search_term: str) -> List[Dict]:
        """Extract companies with specific insurance problems from news"""
        signals = []
        try:
            # More specific patterns for companies with insurance issues
            problem_patterns = [
                r'([A-Z][a-zA-Z\s]+(?:Inc|Corp|LLC|Ltd|Co\.?))[\s\w]*(?:denied|canceled|expired|increased|struggling)',
                r'(?:denied|canceled|expired)[\s\w]*([A-Z][a-zA-Z\s]+(?:Inc|Corp|LLC|Ltd|Co\.?))',
                r'([A-Z][a-zA-Z\s]{3,30})[\s\w]*(?:cyber insurance|coverage)[\s\w]*(?:denied|problem|issue)'
            ]
            
            # Signal strength based on problem type
            problem_severity = {
                'denied': 0.9,
                'canceled': 0.8,
                'expired': 0.7,
                'increased': 0.6,
                'struggling': 0.8
            }
            
            for pattern in problem_patterns:
                matches = re.findall(pattern, rss_text, re.IGNORECASE)
                for match in matches[:2]:  # Quality over quantity
                    if isinstance(match, tuple):
                        match = match[0]
                    
                    if len(match.strip()) > 5 and len(match.strip()) < 50:
                        # Determine signal strength based on problem type
                        strength = 0.7  # default
                        for problem, score in problem_severity.items():
                            if problem in search_term.lower():
                                strength = score
                                break
                        
                        signal = {
                            'company_name': match.strip(),
                            'domain': self.estimate_domain(match.strip()),
                            'signal_type': 'insurance_coverage_issue',
                            'signal_date': datetime.utcnow().isoformat(),
                            'signal_strength': strength,
                            'raw_data': {
                                'issue_type': search_term,
                                'news_source': 'targeted_search',
                                'detection_method': 'insurance_problem_detection',
                                'urgency': 'high' if strength > 0.7 else 'medium'
                            },
                            'source': 'insurance_issues'
                        }
                        signals.append(signal)
                        print(f"Found insurance issue for: {match.strip()} ({search_term})")
        except Exception as e:
            print(f"Error extracting companies with insurance issues: {e}")
        
        return signals
    
    def analyze_existing_companies_for_risks(self) -> List[Dict]:
        """Analyze existing companies in database for insurance risk factors"""
        signals = []
        
        try:
            # Get companies from database that need insurance risk analysis
            try:
                companies = self.clay_client.query_table(
                    'company_universe',
                    {'insurance_risk_analyzed': False}
                )
            except Exception as e:
                print(f"Error querying companies for risk analysis: {e}")
                return signals
            
            if not companies:
                print("No companies need insurance risk analysis")
                return signals
            
            if not isinstance(companies, list):
                try:
                    companies = list(companies) if companies else []
                except:
                    return signals
            
            # Analyze up to 15 companies per run
            companies = companies[:15]
            print(f"Analyzing {len(companies)} companies for insurance risks")
            
            company_updates = []
            
            for company in companies:
                if not isinstance(company, dict):
                    continue
                    
                domain = company.get('domain')
                company_name = company.get('company_name', '')
                
                if not domain or not company_name:
                    continue
                
                # Calculate comprehensive insurance risk score
                risk_analysis = self.calculate_insurance_risk_score(company)
                
                if risk_analysis and risk_analysis.get('signal_strength', 0) > 0.6:
                    signal = {
                        'company_name': company_name,
                        'domain': domain,
                        'signal_type': 'high_insurance_risk',
                        'signal_date': datetime.utcnow().isoformat(),
                        'signal_strength': risk_analysis['signal_strength'],
                        'raw_data': risk_analysis,
                        'source': 'risk_analysis'
                    }
                    signals.append(signal)
                    print(f"High insurance risk identified: {company_name} (score: {risk_analysis['signal_strength']:.2f})")
                
                # Mark as analyzed
                company_updates.append({
                    'company_name': company_name,
                    'domain': domain,
                    'insurance_risk_analyzed': True,
                    'last_risk_analysis': datetime.utcnow().isoformat(),
                    'risk_score': risk_analysis.get('signal_strength', 0) if risk_analysis else 0
                })
            
            # Update companies as analyzed
            if company_updates:
                try:
                    self.clay_client.bulk_upsert('company_universe', company_updates)
                    print(f"Updated {len(company_updates)} companies with risk analysis")
                except Exception as e:
                    print(f"Error updating risk analysis status: {e}")
                    
        except Exception as e:
            print(f"Error in insurance risk analysis: {e}")
        
        return signals
    
    def calculate_insurance_risk_score(self, company: Dict) -> Dict:
        """Calculate comprehensive insurance risk score for a company"""
        try:
            domain = company.get('domain', '')
            company_name = company.get('company_name', '')
            
            risk_score = 0.3  # Base score
            risk_factors = []
            
            # Factor 1: Recent security incidents (major factor)
            if self.has_recent_breach_signals(domain):
                risk_score += 0.4
                risk_factors.append("recent_breach_history")
            
            # Factor 2: High-risk industry
            if self.is_high_risk_industry(company_name):
                risk_score += 0.2
                risk_factors.append("high_risk_industry")
            
            # Factor 3: Company size (larger = more risk)
            if self.estimate_company_size(domain, company_name) == 'enterprise':
                risk_score += 0.1
                risk_factors.append("enterprise_size")
            
            # Factor 4: Multiple threat signals
            threat_count = self.count_threat_signals(domain)
            if threat_count > 2:
                risk_score += 0.2
                risk_factors.append("multiple_threats")
            elif threat_count > 0:
                risk_score += 0.1
                risk_factors.append("some_threats")
            
            # Factor 5: Time since last incident (recent = higher risk)
            days_since_incident = self.days_since_last_incident(domain)
            if days_since_incident is not None:
                if days_since_incident < 30:
                    risk_score += 0.2
                    risk_factors.append("very_recent_incident")
                elif days_since_incident < 90:
                    risk_score += 0.1
                    risk_factors.append("recent_incident")
            
            # Cap at 1.0
            risk_score = min(risk_score, 1.0)
            
            if risk_score > 0.6:
                return {
                    'signal_strength': risk_score,
                    'risk_factors': risk_factors,
                    'threat_count': threat_count,
                    'days_since_incident': days_since_incident,
                    'recommendation': self.get_insurance_recommendation(risk_factors),
                    'urgency_level': 'high' if risk_score > 0.8 else 'medium'
                }
            
        except Exception as e:
            print(f"Error calculating risk score for {company.get('domain', 'unknown')}: {e}")
        
        return None
    
    def count_threat_signals(self, domain: str) -> int:
        """Count total threat signals for a domain"""
        try:
            signals = self.clay_client.query_table(
                'pain_signals',
                {'domain': domain}
            )
            return len(signals) if signals else 0
        except:
            return 0
    
    def days_since_last_incident(self, domain: str) -> int:
        """Calculate days since last security incident"""
        try:
            signals = self.clay_client.query_table(
                'pain_signals',
                {'domain': domain}
            )
            
            if not signals:
                return None
            
            # Find most recent incident
            most_recent = None
            for signal in signals:
                signal_date_str = signal.get('signal_date', '')
                if signal_date_str:
                    try:
                        signal_date = datetime.fromisoformat(signal_date_str.replace('Z', '+00:00'))
                        if most_recent is None or signal_date > most_recent:
                            most_recent = signal_date
                    except:
                        continue
            
            if most_recent:
                return (datetime.utcnow().replace(tzinfo=most_recent.tzinfo) - most_recent).days
            
        except:
            pass
        return None
    
    def get_insurance_recommendation(self, risk_factors: List[str]) -> str:
        """Get specific insurance recommendation based on risk factors"""
        if 'recent_breach_history' in risk_factors:
            return "immediate_coverage_review_post_breach"
        elif 'multiple_threats' in risk_factors:
            return "comprehensive_security_insurance_audit"
        elif 'high_risk_industry' in risk_factors:
            return "industry_specific_coverage_assessment"
        else:
            return "general_policy_optimization"
    
    def estimate_domain(self, company_name: str) -> str:
        """Estimate domain from company name"""
        clean_name = re.sub(r'[^\w\s]', '', company_name.lower())
        clean_name = re.sub(r'\s+(inc|llc|corp|corporation|ltd|limited|company|co)$', '', clean_name)
        clean_name = clean_name.replace(' ', '')
        return f"{clean_name}.com"
    
    def push_to_clay(self, signals: List[Dict]):
        """Push insurance signals to Clay webhook in batches"""
        from config.settings import config
        
        if not config.CLAY_WEBHOOK_URL:
            print("Warning: No Clay webhook URL configured")
            return
        
        if not signals:
            print("No insurance signals to send")
            return
        
        # Send data in smaller batches
        batch_size = 25  # Smaller batches for insurance data
        total_batches = (len(signals) + batch_size - 1) // batch_size
        
        print(f"Sending {len(signals)} insurance signals in {total_batches} batches of {batch_size}")
        
        successful_batches = 0
        failed_batches = 0
        
        for i in range(0, len(signals), batch_size):
            batch = signals[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            # Prepare webhook payload for this batch
            webhook_data = {
                'event_type': 'insurance_intelligence_collection',
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'insurance_intel',
                'batch_info': {
                    'batch_number': batch_num,
                    'total_batches': total_batches,
                    'batch_size': len(batch),
                    'total_records': len(signals)
                },
                'data': {
                    'companies': [],
                    'pain_signals': []
                },
                'summary': {
                    'batch_signals': len(batch),
                    'signal_types': list(set([s['signal_type'] for s in batch])),
                    'sources': list(set([s['source'] for s in batch]))
                }
            }
            
            for signal in batch:
                # Prepare company record
                company = {
                    'company_name': signal['company_name'],
                    'domain': signal['domain'],
                    'data_source': signal['source'],
                    'last_updated': datetime.utcnow().isoformat()
                }
                webhook_data['data']['companies'].append(company)
                
                # Prepare signal record
                pain_signal = {
                    'domain': signal['domain'],
                    'signal_type': signal['signal_type'],
                    'signal_date': signal['signal_date'],
                    'signal_strength': signal['signal_strength'],
                    'raw_data': signal['raw_data'],
                    'source': signal['source']
                }
                webhook_data['data']['pain_signals'].append(pain_signal)
            
            # Send this batch to Clay webhook
            print(f"Sending batch {batch_num}/{total_batches} ({len(batch)} records)...")
            if self.send_to_webhook(webhook_data):
                successful_batches += 1
            else:
                failed_batches += 1
        
        print(f"Batch sending complete: {successful_batches} successful, {failed_batches} failed")
    
    def send_to_webhook(self, data: Dict) -> bool:
        """Send data to Clay webhook with authentication"""
        from config.settings import config
        import hashlib
        import hmac
        
        try:
            webhook_url = config.CLAY_WEBHOOK_URL
            payload = json.dumps(data, indent=2)
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'BTA-InsuranceIntel/1.0'
            }
            
            if config.CLAY_WEBHOOK_SECRET:
                signature = hmac.new(
                    config.CLAY_WEBHOOK_SECRET.encode(),
                    payload.encode(),
                    hashlib.sha256
                ).hexdigest()
                headers['X-Webhook-Signature'] = f'sha256={signature}'
            
            response = self.session.post(
                webhook_url,
                data=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"✅ Batch sent successfully")
                return True
            else:
                print(f"❌ Batch failed - Status {response.status_code}: {response.text[:100]}")
                return False
                
        except Exception as e:
            print(f"❌ Batch failed - Error: {e}")
            return False
    
    def run_collection(self):
        """Main entry point for insurance intelligence collection"""
        print("Starting insurance intelligence collection...")
        
        # Collect all insurance signals
        all_signals = self.collect_insurance_signals()
        
        print(f"Found {len(all_signals)} insurance intelligence signals")
        
        # Push to Clay webhook
        self.push_to_clay(all_signals)
        
        print("Insurance intelligence collection complete")
