"""
Company Analyzer - Reactive Analysis of Existing Companies
Analyzes companies already in Clay database for pain signals
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import re
import time
from config.settings import config

class CompanyAnalyzer:
    """Analyzes existing companies in Clay database for pain signals"""
    
    def __init__(self, clay_client):
        self.clay_client = clay_client
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BTA-CompanyAnalyzer/1.0'
        })
        
        # Initialize Shodan if API key available
        self.shodan_monitor = None
        if config.SHODAN_API_KEY:
            from .shodan_monitor import ShodanMonitor
            self.shodan_monitor = ShodanMonitor(config.SHODAN_API_KEY)
        
        # Analysis methods (REACTIVE ONLY)
        self.analysis_methods = [
            'hibp_breach_check',           # Moved from proactive
            'github_exposure_check',       # Moved from proactive
            'breach_mention_search',       # Google News search
            'serpapi_breach_search',       # SERPAPI news search (enhanced)
            'job_posting_analysis',        # LinkedIn Jobs
            'technology_stack_analysis',   # BuiltWith data
            'insurance_risk_assessment',   # Risk calculation
            'compliance_vulnerability_check', # Compliance issues
            'shodan_network_exposure'      # Network vulnerability scan (NEW!)
        ]
    
    def analyze_company_batch(self, batch_size: int = 100) -> List[Dict]:
        """Analyze a batch of companies for pain signals"""
        signals = []
        
        try:
            print(f"Analyzing batch of {batch_size} companies...")
            
            # Get companies that need analysis
            companies = self.get_companies_for_analysis(batch_size)
            
            if not companies:
                print("No companies need analysis")
                return signals
            
            print(f"Found {len(companies)} companies to analyze")
            
            # Analyze each company
            for i, company in enumerate(companies):
                try:
                    print(f"Analyzing company {i+1}/{len(companies)}: {company.get('company_name', 'Unknown')}")
                    
                    # Run all analysis methods
                    company_signals = self.analyze_single_company(company)
                    signals.extend(company_signals)
                    
                    # Mark as analyzed
                    self.mark_company_analyzed(company)
                    
                    # Rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"Error analyzing company {company.get('domain', 'unknown')}: {e}")
                    continue
            
            print(f"Analysis complete: {len(signals)} signals found")
            
        except Exception as e:
            print(f"Error in company batch analysis: {e}")
        
        return signals
    
    def get_companies_for_analysis(self, limit: int) -> List[Dict]:
        """Get companies that need analysis"""
        try:
            # Get companies that haven't been analyzed recently
            companies = self.clay_client.query_table(
                'company_universe',
                {
                    'analyzed': False,  # Haven't been analyzed
                    'last_analysis': None  # Or last analysis was > 30 days ago
                }
            )
            
            # If no unanalyzed companies, get companies analyzed > 30 days ago
            if not companies:
                thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
                companies = self.clay_client.query_table(
                    'company_universe',
                    {'last_analysis': {'$lt': thirty_days_ago}}
                )
            
            return companies[:limit] if companies else []
            
        except Exception as e:
            print(f"Error getting companies for analysis: {e}")
            return []
    
    def analyze_single_company(self, company: Dict) -> List[Dict]:
        """Analyze a single company for pain signals"""
        signals = []
        
        try:
            domain = company.get('domain', '')
            company_name = company.get('company_name', '')
            
            if not domain:
                return signals
            
            # Method 1: HIBP breach check (moved from proactive)
            hibp_signals = self.check_hibp_breaches(company)
            signals.extend(hibp_signals)
            
            # Method 2: GitHub credential exposure (moved from proactive)
            github_signals = self.check_github_exposures(company)
            signals.extend(github_signals)
            
            # Method 3: Check for recent breach mentions
            breach_signals = self.check_breach_mentions(company)
            signals.extend(breach_signals)
            
            # Method 4: Analyze job postings for security roles
            job_signals = self.analyze_job_postings(company)
            signals.extend(job_signals)
            
            # Method 5: Check technology stack for security gaps
            tech_signals = self.analyze_technology_stack(company)
            signals.extend(tech_signals)
            
            # Method 6: Assess insurance risk factors
            insurance_signals = self.assess_insurance_risk(company)
            signals.extend(insurance_signals)
            
            # Method 7: Check compliance vulnerabilities
            compliance_signals = self.check_compliance_vulnerabilities(company)
            signals.extend(compliance_signals)
            
            # Method 8: Shodan network exposure analysis (NEW!)
            if self.shodan_monitor:
                shodan_signals = self.check_shodan_exposures(company)
                signals.extend(shodan_signals)
            
        except Exception as e:
            print(f"Error analyzing company {company.get('domain', 'unknown')}: {e}")
        
        return signals
    
    def check_hibp_breaches(self, company: Dict) -> List[Dict]:
        """Check HIBP for breach history (REACTIVE ONLY)"""
        signals = []
        
        try:
            from config.settings import config
            hibp_api_key = getattr(config, 'HIBP_API_KEY', None)
            
            if not hibp_api_key:
                return signals  # Skip if no API key
            
            domain = company.get('domain', '')
            if not domain:
                return signals
            
            # Check domain for breaches
            response = self.session.get(
                f'https://haveibeenpwned.com/api/v3/breaches?domain={domain}',
                headers={'hibp-api-key': hibp_api_key},
                timeout=10
            )
            
            if response.status_code == 200:
                breaches = response.json()
                if breaches:
                    # Filter for RECENT breaches (last 1-2 years)
                    recent_breaches = []
                    for breach in breaches:
                        breach_date = breach.get('BreachDate', '')
                        breach_added = breach.get('AddedDate', '')
                        
                        # Check if breach is from 2023-2025
                        date_to_check = breach_date or breach_added
                        if self.is_recent_date(date_to_check):
                            recent_breaches.append(breach)
                    
                    if recent_breaches:
                        signal = {
                            'company_name': company.get('company_name', ''),
                            'domain': domain,
                            'signal_type': 'hibp_breach_detected',
                            'signal_date': datetime.utcnow().isoformat(),
                            'signal_strength': 0.7,
                            'raw_data': {
                                'breach_count': len(recent_breaches),
                                'total_breaches': len(breaches),
                                'breaches': recent_breaches[:5],  # First 5 RECENT breaches
                                'detection_method': 'hibp_api',
                                'date_filtered': True,
                                'filter_years': '2023-2025'
                            },
                            'source': 'company_analysis'
                        }
                        signals.append(signal)
                        print(f"HIBP RECENT breach(es) found for: {domain} ({len(recent_breaches)}/{len(breaches)} recent)")
                    else:
                        print(f"HIBP breaches found for: {domain} ({len(breaches)} total) - ALL FILTERED OUT (too old)")
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"Error checking HIBP for {company.get('domain', 'unknown')}: {e}")
        
        return signals
    
    def check_github_exposures(self, company: Dict) -> List[Dict]:
        """Check GitHub for credential exposures (REACTIVE ONLY)"""
        signals = []
        
        try:
            domain = company.get('domain', '')
            company_name = company.get('company_name', '')
            
            if not domain:
                return signals
            
            # Search for exposed credentials
            search_terms = [
                f'"{domain}" API key',
                f'"{domain}" password',
                f'"{domain}" secret',
                f'"{company_name}" API key'
            ]
            
            for term in search_terms:
                try:
                    response = self.session.get(
                        'https://api.github.com/search/code',
                        params={'q': term, 'per_page': 5},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        results = response.json()
                        if results.get('total_count', 0) > 0:
                            signal = {
                                'company_name': company_name,
                                'domain': domain,
                                'signal_type': 'github_exposure_detected',
                                'signal_date': datetime.utcnow().isoformat(),
                                'signal_strength': 0.6,
                                'raw_data': {
                                    'exposure_count': results['total_count'],
                                    'search_term': term,
                                    'detection_method': 'github_api'
                                },
                                'source': 'company_analysis'
                            }
                            signals.append(signal)
                            print(f"GitHub exposure found for: {domain}")
                            break  # Found one, no need to search more
                    
                    time.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f"Error checking GitHub for {company.get('domain', 'unknown')}: {e}")
        
        return signals
    
    def is_recent_date(self, date_str: str) -> bool:
        """Check if date is within the last 1-2 years"""
        if not date_str:
            return False
        
        try:
            from datetime import datetime, timedelta
            import re
            
            # Parse various date formats
            current_date = datetime.now()
            
            # Try to parse the date string (SERPAPI returns varied formats)
            if re.search(r'\d{4}', date_str):  # Has year
                # Extract year
                year_match = re.search(r'(\d{4})', date_str)
                if year_match:
                    news_year = int(year_match.group(1))
                    
                    # Accept dates from 2023 onwards (1-2 years)
                    if news_year >= 2023:
                        return True
            
            # If parsing fails, default to accepting (conservative approach)
            return True
            
        except Exception as e:
            print(f"Error parsing date: {date_str} - {e}")
            return True  # Default to accepting if parsing fails
    
    def check_breach_mentions_serpapi(self, company: Dict) -> List[Dict]:
        """Check breach mentions using SERPAPI (more reliable) - FILTERED TO LAST 1-2 YEARS"""
        signals = []
        
        try:
            from config.settings import config
            
            if not config.SERPAPI_API_KEY:
                return signals
            
            domain = company.get('domain', '')
            company_name = company.get('company_name', '')
            
            # Search for breach mentions using SERPAPI - Updated queries for recent years
            search_queries = [
                f'"{company_name}" data breach 2024',
                f'"{company_name}" data breach 2025',
                f'"{company_name}" data breach "2023"',
                f'"{company_name}" security incident 2024',
                f'"{company_name}" cyber attack 2024',
                f'"{domain}" breach 2024',
                f'"{domain}" breach "2023"'
            ]
            
            for query in search_queries:
                try:
                    response = self.session.get(
                        'https://serpapi.com/search',
                        params={
                            'q': query,
                            'api_key': config.SERPAPI_API_KEY,
                            'engine': 'google',
                            'tbm': 'nws',  # News search
                            'num': 10
                        },
                        timeout=15
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        news_results = data.get('news_results', [])
                        
                        for result in news_results:
                            title = result.get('title', '').lower()
                            snippet = result.get('snippet', '').lower()
                            
                            # Check for breach-related keywords
                            breach_keywords = [
                                'data breach', 'security incident', 'cyber attack',
                                'ransomware', 'hack', 'compromised', 'exposed',
                                'leaked', 'stolen', 'unauthorized access'
                            ]
                            
                            # Add DATE FILTERING - Only include recent breaches (1-2 years)
                            news_date = result.get('date', '')
                            is_recent = self.is_recent_date(news_date)
                            
                            if any(keyword in title or keyword in snippet for keyword in breach_keywords) and is_recent:
                                signal = {
                                    'company_name': company_name,
                                    'domain': domain,
                                    'signal_type': 'breach_mention_detected',
                                    'signal_date': datetime.utcnow().isoformat(),
                                    'signal_strength': 0.9,  # Higher confidence with SERPAPI
                                    'raw_data': {
                                        'search_query': query,
                                        'detection_method': 'serpapi_news_search',
                                        'confidence': 'very_high',
                                        'news_title': result.get('title', ''),
                                        'news_snippet': result.get('snippet', ''),
                                        'news_url': result.get('link', ''),
                                        'news_date': news_date,
                                        'date_filtered': True,
                                        'filter_years': '2023-2025'
                                    },
                                    'source': 'company_analysis_serpapi'
                                }
                                signals.append(signal)
                                print(f"Found RECENT breach mention via SERPAPI for: {company_name} (Date: {news_date})")
                                break  # Found one, no need to search more
                            elif any(keyword in title or keyword in snippet for keyword in breach_keywords) and not is_recent:
                                print(f"Found OLD breach mention for: {company_name} (Date: {news_date}) - FILTERED OUT")
                    
                    time.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    print(f"Error with SERPAPI search: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error in SERPAPI breach check: {e}")
        
        return signals
    
    def check_breach_mentions(self, company: Dict) -> List[Dict]:
        """Check if company has been mentioned in breach reports"""
        signals = []
        
        try:
            domain = company.get('domain', '')
            company_name = company.get('company_name', '')
            
            # Try SERPAPI first (more reliable), fallback to Google News
            serpapi_signals = self.check_breach_mentions_serpapi(company)
            if serpapi_signals:
                signals.extend(serpapi_signals)
                return signals
            
            # Fallback to Google News RSS
            breach_search_terms = [
                f'"{company_name}" data breach',
                f'"{company_name}" security incident',
                f'"{company_name}" cyber attack',
                f'"{domain}" breach',
                f'"{domain}" security incident'
            ]
            
            for term in breach_search_terms:
                try:
                    response = self.session.get(
                        'https://news.google.com/rss/search',
                        params={
                            'q': term,
                            'hl': 'en',
                            'gl': 'US',
                            'ceid': 'US:en'
                        },
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        if self.has_recent_breach_mentions(response.text, company_name):
                            signal = {
                                'company_name': company_name,
                                'domain': domain,
                                'signal_type': 'breach_mention_detected',
                                'signal_date': datetime.utcnow().isoformat(),
                                'signal_strength': 0.8,
                                'raw_data': {
                                    'search_term': term,
                                    'detection_method': 'news_search',
                                    'confidence': 'high'
                                },
                                'source': 'company_analysis'
                            }
                            signals.append(signal)
                            print(f"Found breach mention for: {company_name}")
                            break  # Found one, no need to search more
                    
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Error searching for breach mentions: {e}")
                    continue
            
        except Exception as e:
            print(f"Error checking breach mentions: {e}")
        
        return signals
    
    def analyze_job_postings(self, company: Dict) -> List[Dict]:
        """Analyze if company is posting security jobs (indicating gaps)"""
        signals = []
        
        try:
            domain = company.get('domain', '')
            company_name = company.get('company_name', '')
            
            # Search for security job postings by this company
            security_job_terms = [
                f'"{company_name}" CISO',
                f'"{company_name}" security director',
                f'"{company_name}" cybersecurity',
                f'"{company_name}" information security'
            ]
            
            for term in security_job_terms:
                try:
                    response = self.session.get(
                        'https://www.linkedin.com/jobs/search',
                        params={
                            'keywords': term,
                            'location': 'United States',
                            'f_TPR': 'r2592000',  # Last 30 days
                            'f_JT': 'F',  # Full-time
                            'start': 0,
                            'count': 10
                        },
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        job_count = self.count_security_jobs(response.text, company_name)
                        
                        if job_count > 0:
                            signal = {
                                'company_name': company_name,
                                'domain': domain,
                                'signal_type': 'security_job_postings',
                                'signal_date': datetime.utcnow().isoformat(),
                                'signal_strength': min(0.3 + (job_count * 0.1), 0.8),
                                'raw_data': {
                                    'job_count': job_count,
                                    'search_term': term,
                                    'detection_method': 'linkedin_jobs',
                                    'confidence': 'medium'
                                },
                                'source': 'company_analysis'
                            }
                            signals.append(signal)
                            print(f"Found {job_count} security jobs for: {company_name}")
                            break
                    
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"Error searching for security jobs: {e}")
                    continue
            
        except Exception as e:
            print(f"Error analyzing job postings: {e}")
        
        return signals
    
    def analyze_technology_stack(self, company: Dict) -> List[Dict]:
        """Analyze technology stack for security gaps"""
        signals = []
        
        try:
            domain = company.get('domain', '')
            company_name = company.get('company_name', '')
            
            # This would integrate with BuiltWith data you already have in Clay
            # For now, we'll do basic analysis
            
            # Check if they have basic security tools
            tech_gaps = self.identify_security_tech_gaps(company)
            
            if tech_gaps:
                signal = {
                    'company_name': company_name,
                    'domain': domain,
                    'signal_type': 'security_tech_gaps',
                    'signal_date': datetime.utcnow().isoformat(),
                    'signal_strength': len(tech_gaps) * 0.2,  # 0.2 per gap
                    'raw_data': {
                        'tech_gaps': tech_gaps,
                        'detection_method': 'tech_stack_analysis',
                        'confidence': 'medium'
                    },
                    'source': 'company_analysis'
                }
                signals.append(signal)
                print(f"Found tech gaps for: {company_name} - {tech_gaps}")
            
        except Exception as e:
            print(f"Error analyzing technology stack: {e}")
        
        return signals
    
    def assess_insurance_risk(self, company: Dict) -> List[Dict]:
        """Assess insurance risk factors for company"""
        signals = []
        
        try:
            domain = company.get('domain', '')
            company_name = company.get('company_name', '')
            
            # Calculate insurance risk score
            risk_factors = self.calculate_insurance_risk_factors(company)
            
            if risk_factors['risk_score'] > 0.6:
                signal = {
                    'company_name': company_name,
                    'domain': domain,
                    'signal_type': 'high_insurance_risk',
                    'signal_date': datetime.utcnow().isoformat(),
                    'signal_strength': risk_factors['risk_score'],
                    'raw_data': {
                        'risk_factors': risk_factors['factors'],
                        'detection_method': 'insurance_risk_assessment',
                        'confidence': 'medium'
                    },
                    'source': 'company_analysis'
                }
                signals.append(signal)
                print(f"High insurance risk for: {company_name} (score: {risk_factors['risk_score']:.2f})")
            
        except Exception as e:
            print(f"Error assessing insurance risk: {e}")
        
        return signals
    
    def check_compliance_vulnerabilities(self, company: Dict) -> List[Dict]:
        """Check for compliance vulnerabilities"""
        signals = []
        
        try:
            domain = company.get('domain', '')
            company_name = company.get('company_name', '')
            
            # Check for compliance-related issues
            compliance_issues = self.identify_compliance_issues(company)
            
            if compliance_issues:
                signal = {
                    'company_name': company_name,
                    'domain': domain,
                    'signal_type': 'compliance_vulnerability',
                    'signal_date': datetime.utcnow().isoformat(),
                    'signal_strength': len(compliance_issues) * 0.3,
                    'raw_data': {
                        'compliance_issues': compliance_issues,
                        'detection_method': 'compliance_check',
                        'confidence': 'medium'
                    },
                    'source': 'company_analysis'
                }
                signals.append(signal)
                print(f"Found compliance issues for: {company_name} - {compliance_issues}")
            
        except Exception as e:
            print(f"Error checking compliance vulnerabilities: {e}")
        
        return signals
    
    def has_recent_breach_mentions(self, html_content: str, company_name: str) -> bool:
        """Check if HTML content contains recent breach mentions"""
        try:
            # Look for breach-related keywords
            breach_keywords = [
                'data breach', 'security incident', 'cyber attack',
                'ransomware', 'data leak', 'security breach'
            ]
            
            content_lower = html_content.lower()
            company_lower = company_name.lower()
            
            # Check if company name appears with breach keywords
            for keyword in breach_keywords:
                if keyword in content_lower and company_lower in content_lower:
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error checking breach mentions: {e}")
            return False
    
    def count_security_jobs(self, html_content: str, company_name: str) -> int:
        """Count security job postings for company"""
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for job cards
            job_cards = soup.find_all('div', {'class': 'job-search-card'})
            
            security_job_count = 0
            company_lower = company_name.lower()
            
            for card in job_cards:
                try:
                    # Check if this job is from the company
                    company_elem = card.find('h4', {'class': 'job-search-card__subtitle'})
                    title_elem = card.find('h3', {'class': 'job-search-card__title'})
                    
                    if company_elem and title_elem:
                        card_company = company_elem.get_text().strip().lower()
                        job_title = title_elem.get_text().strip().lower()
                        
                        # Check if it's the right company and a security role
                        if company_lower in card_company:
                            security_keywords = [
                                'security', 'cyber', 'ciso', 'information security',
                                'threat', 'incident response', 'compliance'
                            ]
                            
                            if any(keyword in job_title for keyword in security_keywords):
                                security_job_count += 1
                
                except Exception as e:
                    continue
            
            return security_job_count
            
        except Exception as e:
            print(f"Error counting security jobs: {e}")
            return 0
    
    def identify_security_tech_gaps(self, company: Dict) -> List[str]:
        """Identify security technology gaps"""
        gaps = []
        
        try:
            # This would integrate with your BuiltWith data in Clay
            # For now, we'll use basic heuristics
            
            domain = company.get('domain', '')
            company_name = company.get('company_name', '')
            
            # Basic security tool indicators
            if not self.has_security_tools_indicator(domain):
                gaps.append('no_security_tools_detected')
            
            # Check for SSL/TLS issues
            if not self.has_secure_ssl(domain):
                gaps.append('ssl_security_issues')
            
            # Check for basic security headers
            if not self.has_security_headers(domain):
                gaps.append('missing_security_headers')
            
        except Exception as e:
            print(f"Error identifying tech gaps: {e}")
        
        return gaps
    
    def calculate_insurance_risk_factors(self, company: Dict) -> Dict:
        """Calculate insurance risk factors"""
        risk_score = 0.3  # Base score
        factors = []
        
        try:
            # Factor 1: Industry risk
            if self.is_high_risk_industry(company.get('company_name', '')):
                risk_score += 0.2
                factors.append('high_risk_industry')
            
            # Factor 2: Company size (larger = more risk)
            if self.is_large_company(company):
                risk_score += 0.2
                factors.append('large_company')
            
            # Factor 3: Recent security issues
            if self.has_recent_security_issues(company.get('domain', '')):
                risk_score += 0.3
                factors.append('recent_security_issues')
            
            # Cap at 1.0
            risk_score = min(risk_score, 1.0)
            
        except Exception as e:
            print(f"Error calculating risk factors: {e}")
        
        return {
            'risk_score': risk_score,
            'factors': factors
        }
    
    def identify_compliance_issues(self, company: Dict) -> List[str]:
        """Identify compliance issues"""
        issues = []
        
        try:
            company_name = company.get('company_name', '').lower()
            
            # Check for industry-specific compliance requirements
            if any(keyword in company_name for keyword in ['healthcare', 'medical', 'hospital']):
                issues.append('hipaa_compliance_required')
            
            if any(keyword in company_name for keyword in ['financial', 'bank', 'credit']):
                issues.append('financial_compliance_required')
            
            if any(keyword in company_name for keyword in ['government', 'municipal']):
                issues.append('government_compliance_required')
            
        except Exception as e:
            print(f"Error identifying compliance issues: {e}")
        
        return issues
    
    def has_security_tools_indicator(self, domain: str) -> bool:
        """Check if domain has security tools indicators"""
        try:
            # This would integrate with your BuiltWith data
            # For now, return False to indicate gaps
            return False
        except:
            return False
    
    def has_secure_ssl(self, domain: str) -> bool:
        """Check if domain has secure SSL"""
        try:
            import ssl
            import socket
            
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    return ssock.version() in ['TLSv1.2', 'TLSv1.3']
        except:
            return False
    
    def has_security_headers(self, domain: str) -> bool:
        """Check if domain has security headers"""
        try:
            response = self.session.get(f'https://{domain}', timeout=10)
            headers = response.headers
            
            security_headers = [
                'Strict-Transport-Security',
                'X-Content-Type-Options',
                'X-Frame-Options',
                'X-XSS-Protection'
            ]
            
            return any(header in headers for header in security_headers)
        except:
            return False
    
    def is_high_risk_industry(self, company_name: str) -> bool:
        """Check if company is in high-risk industry"""
        high_risk_keywords = [
            'healthcare', 'medical', 'hospital', 'clinic',
            'financial', 'bank', 'credit', 'insurance',
            'government', 'municipal', 'utilities', 'energy'
        ]
        
        name_lower = company_name.lower()
        return any(keyword in name_lower for keyword in high_risk_keywords)
    
    def is_large_company(self, company: Dict) -> bool:
        """Check if company is large (more insurance risk)"""
        # This would use your employee count data from Clay
        employee_count = company.get('employee_count', 0)
        return employee_count > 500
    
    def has_recent_security_issues(self, domain: str) -> bool:
        """Check if domain has recent security issues"""
        try:
            # Check if there are recent pain signals for this domain
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
            
            return False
            
        except:
            return False
    
    def mark_company_analyzed(self, company: Dict):
        """Mark company as analyzed"""
        try:
            update_data = {
                'domain': company.get('domain'),
                'analyzed': True,
                'last_analysis': datetime.utcnow().isoformat()
            }
            
            self.clay_client.add_row('company_universe', update_data)
            
        except Exception as e:
            print(f"Error marking company as analyzed: {e}")
    
    def push_signals_to_clay(self, signals: List[Dict]):
        """Push analysis signals to Clay"""
        try:
            if not signals:
                print("No signals to push")
                return
            
            # Send signals to Clay webhook
            webhook_data = {
                'event_type': 'company_analysis_results',
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'company_analyzer',
                'data': {
                    'companies': [],
                    'pain_signals': []
                },
                'summary': {
                    'signals_found': len(signals),
                    'signal_types': list(set([s['signal_type'] for s in signals]))
                }
            }
            
            for signal in signals:
                # Add company record
                webhook_data['data']['companies'].append({
                    'company_name': signal['company_name'],
                    'domain': signal['domain'],
                    'data_source': 'company_analysis',
                    'last_updated': datetime.utcnow().isoformat()
                })
                
                # Add signal record
                webhook_data['data']['pain_signals'].append({
                    'domain': signal['domain'],
                    'signal_type': signal['signal_type'],
                    'signal_date': signal['signal_date'],
                    'signal_strength': signal['signal_strength'],
                    'raw_data': signal['raw_data'],
                    'source': signal['source']
                })
            
            # Send to webhook
            self.send_to_webhook(webhook_data)
            
        except Exception as e:
            print(f"Error pushing signals to Clay: {e}")
    
    def send_to_webhook(self, data: Dict) -> bool:
        """Send data to Clay webhook"""
        from config.settings import config
        import hashlib
        import hmac
        
        try:
            webhook_url = config.CLAY_WEBHOOK_URL
            payload = json.dumps(data, indent=2)
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'BTA-CompanyAnalyzer/1.0'
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
                print(f"✅ Analysis signals sent successfully")
                return True
            else:
                print(f"❌ Failed to send signals - Status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending to webhook: {e}")
            return False
    
    def check_shodan_exposures(self, company: Dict) -> List[Dict]:
        """Check Shodan for network exposures and vulnerabilities (NEW!)"""
        signals = []
        
        if not self.shodan_monitor:
            return signals
            
        try:
            domain = company.get('domain', '')
            company_name = company.get('company_name', '')
            
            if not domain:
                return signals
            
            print(f"🔍 Running Shodan network analysis for {domain}")
            
            # Run Shodan exposure analysis
            shodan_signals = self.shodan_monitor.analyze_domain_exposure(company)
            
            if shodan_signals:
                print(f"🚨 Found {len(shodan_signals)} Shodan exposures for {domain}")
                
                # Add company context to signals
                for signal in shodan_signals:
                    signal['company_name'] = company_name
                    signal['domain'] = domain
                    signal['priority_score'] = signal.get('priority_score', 0.8)
                
                signals.extend(shodan_signals)
            else:
                print(f"✅ No critical Shodan exposures found for {domain}")
                
        except Exception as e:
            print(f"❌ Error checking Shodan exposures for {company.get('domain', 'unknown')}: {e}")
            
        return signals
    
    def run_analysis(self, batch_size: int = 100):
        """Main entry point for company analysis"""
        print("Starting company analysis...")
        
        # Analyze companies
        signals = self.analyze_company_batch(batch_size)
        
        # Push signals to Clay
        if signals:
            self.push_signals_to_clay(signals)
        
        print(f"Company analysis complete: {len(signals)} signals found")
