# src/collectors/free_darkweb_monitor.py
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import logging
import time
import re
from urllib.parse import urljoin

# Configure logger for this module
logger = logging.getLogger(__name__)

class FreeThreatsMonitor:
    """
    Replaces DarkOwl with free/low-cost alternatives
    Primary focus: Ransomware victims (highest signal value)
    """
    def __init__(self, clay_client):
        self.clay_client = clay_client
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BTA-ThreatMonitor/1.0'
        })
        # Rate limiting
        self.last_github_request = 0
        self.github_rate_limit_delay = 1.0  # seconds between requests
        
    def collect_all_threats(self) -> List[Dict]:
        """Main collection method - PROACTIVE ONLY (ransomware victims)"""
        all_signals = []
        
        # PROACTIVE: Only collect ransomware victims (highest value, free)
        all_signals.extend(self.check_ransomware_victims())
        
        # REACTIVE: HIBP and GitHub moved to reactive analysis API
        # These are now handled by the HTTP API when you send companies
        
        return all_signals
    
    def check_ransomware_victims(self) -> List[Dict]:
        """
        Check ransomware.live for active victims
        This is the HIGHEST VALUE signal - companies under active attack
        """
        signals = []
        
        try:
            logger.info("Checking ransomware.live for recent victims...")
            
            # Free API - no key needed
            response = self.session.get(
                'https://api.ransomware.live/recentvictims',
                timeout=15
            )
            
            if response.status_code != 200:
                logger.error(f"Ransomware.live API returned status {response.status_code}: {response.text[:200]}")
                return signals
                
            victims = response.json()
            
            # Handle different response formats
            if isinstance(victims, dict):
                if 'victims' in victims:
                    victims = victims['victims']
                elif 'data' in victims:
                    victims = victims['data']
                else:
                    # Try to find the list in the response
                    victims = []
                    
            if not isinstance(victims, list):
                logger.error(f"Unexpected response format from ransomware.live: {type(victims)}")
                return signals
            
            logger.info(f"Found {len(victims)} potential ransomware victims")
            
            for victim in victims:
                if not isinstance(victim, dict):
                    continue
                    
                # Parse victim data with validation
                company_name = victim.get('post_title', '') or victim.get('title', '') or victim.get('name', '')
                
                if not company_name or len(company_name.strip()) < 2:
                    continue  # Skip invalid company names
                    
                company_name = company_name.strip()
                group = victim.get('group_name', 'Unknown')
                discovered = victim.get('discovered') or victim.get('date') or victim.get('published')
                
                # Parse discovery date with better error handling
                discovery_date = datetime.utcnow()
                if discovered:
                    try:
                        # Handle various date formats
                        if isinstance(discovered, str):
                            # Remove timezone suffixes and normalize
                            discovered_clean = discovered.replace('Z', '+00:00')
                            if '+' not in discovered_clean and discovered_clean.endswith('T'):
                                discovered_clean = discovered_clean[:-1]
                            discovery_date = datetime.fromisoformat(discovered_clean)
                        elif isinstance(discovered, (int, float)):
                            # Unix timestamp
                            discovery_date = datetime.fromtimestamp(discovered)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Could not parse date '{discovered}' for {company_name}: {e}")
                        discovery_date = datetime.utcnow()
                
                hours_since = (datetime.utcnow() - discovery_date).total_seconds() / 3600
                
                # Skip very old entries (older than 30 days)
                if hours_since > 24 * 30:
                    continue
                
                # Estimate domain
                estimated_domain = self.estimate_domain(company_name)
                
                # Create signal
                signal = {
                    'company_name': company_name,
                    'domain': estimated_domain,
                    'signal_type': 'active_ransomware',
                    'signal_date': discovery_date.isoformat(),
                    'signal_strength': 1.0,  # Maximum - they're being ransomed NOW
                    'raw_data': {
                        'ransomware_group': group,
                        'hours_since_posting': round(hours_since, 1),
                        'leak_site_url': victim.get('post_url', '') or victim.get('url', ''),
                        'discovered': discovered,
                        'original_data': victim  # Keep original for debugging
                    },
                    'source': 'ransomware.live'
                }
                signals.append(signal)
                
                logger.warning(f"CRITICAL: Found ransomware victim: {company_name} ({estimated_domain}) by {group}")
        
        except requests.RequestException as e:
            logger.error(f"Network error checking ransomware.live: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from ransomware.live: {e}")
        except Exception as e:
            logger.error(f"Unexpected error checking ransomware sites: {e}")
        
        logger.info(f"Collected {len(signals)} ransomware victim signals")
        return signals
    
    def _rate_limit_github(self) -> None:
        """Enforce rate limiting for GitHub API"""
        current_time = time.time()
        time_since_last = current_time - self.last_github_request
        
        if time_since_last < self.github_rate_limit_delay:
            sleep_time = self.github_rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_github_request = time.time()
    
    def check_github_exposures(self) -> List[Dict]:
        """
        Search GitHub for exposed credentials (FREE)
        Uses unauthenticated API with rate limiting
        """
        signals = []
        
        try:
            logger.info("Checking GitHub for credential exposures...")
            
            # Get companies to check from Clay with error handling
            try:
                companies = self.clay_client.query_table(
                    'company_universe',
                    {'checked_github': False}
                )
            except Exception as e:
                logger.error(f"Error querying companies for GitHub check: {e}")
                return signals
            
            # Validate and limit companies
            if not companies:
                logger.info("No companies need GitHub exposure checking")
                return signals
                
            if not isinstance(companies, list):
                try:
                    companies = list(companies) if companies else []
                except Exception:
                    logger.error("Invalid company data format from Clay query")
                    return signals
            
            # Limit to avoid rate limits
            companies = companies[:5]  # Reduced from 10
            logger.info(f"Checking {len(companies)} companies for GitHub exposures")
            
            company_updates = []
            
            for i, company in enumerate(companies):
                if not isinstance(company, dict):
                    continue
                    
                domain = company.get('domain')
                company_name = company.get('company_name', '')
                
                if not domain or not company_name:
                    logger.warning(f"Skipping company with missing domain/name: {company}")
                    continue
                
                logger.info(f"Checking GitHub exposures for {company_name} ({domain}) [{i+1}/{len(companies)}]")
                
                # Define exposure search queries
                exposure_queries = [
                    f'"{domain}" password',
                    f'"{domain}" api_key',
                    f'"{company_name}" AWS_SECRET',
                    f'"{domain}" connectionString'
                ]
                
                found_exposure = False
                for query in exposure_queries:
                    try:
                        # Rate limit requests
                        self._rate_limit_github()
                        
                        # GitHub search API call
                        response = self.session.get(
                            'https://api.github.com/search/code',
                            params={'q': query, 'per_page': 3},
                            headers={'Accept': 'application/vnd.github.v3+json'},
                            timeout=15
                        )
                        
                        # Handle rate limiting
                        if response.status_code == 403:
                            logger.warning(f"GitHub rate limit hit for {company_name}. Response: {response.text[:100]}")
                            # Stop processing this batch to avoid further rate limiting
                            break
                        
                        if response.status_code == 422:
                            logger.debug(f"Invalid search query for {company_name}: {query}")
                            continue
                            
                        if response.status_code != 200:
                            logger.warning(f"GitHub API returned {response.status_code} for {company_name}")
                            continue
                        
                        try:
                            results = response.json()
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON response from GitHub for {company_name}")
                            continue
                        
                        total_count = results.get('total_count', 0)
                        if total_count > 0:
                            # Found potential credential exposure
                            signal = {
                                'company_name': company_name,
                                'domain': domain,
                                'signal_type': 'github_exposure',
                                'signal_date': datetime.utcnow().isoformat(),
                                'signal_strength': 0.7,
                                'raw_data': {
                                    'exposure_type': 'credentials',
                                    'repository_count': total_count,
                                    'search_query': query,
                                    'items_found': len(results.get('items', []))
                                },
                                'source': 'github'
                            }
                            signals.append(signal)
                            logger.warning(f"Found GitHub credential exposure for {company_name}: {total_count} repositories")
                            found_exposure = True
                            break  # One exposure is sufficient
                    
                    except requests.RequestException as e:
                        logger.error(f"Network error during GitHub search for {company_name}: {e}")
                        break
                    except Exception as e:
                        logger.error(f"Unexpected error in GitHub search for {company_name}: {e}")
                
                # Mark company as checked regardless of results
                company_updates.append({
                    'company_name': company_name,
                    'domain': domain,
                    'checked_github': True,
                    'last_checked_github': datetime.utcnow().isoformat(),
                    'github_exposure_found': found_exposure
                })
            
            # Bulk update companies in Clay
            if company_updates:
                try:
                    self.clay_client.bulk_upsert('company_universe', company_updates)
                    logger.info(f"Updated {len(company_updates)} companies as GitHub-checked")
                except Exception as e:
                    logger.error(f"Error updating company GitHub check status: {e}")
        
        except Exception as e:
            logger.error(f"Unexpected error in GitHub exposure check: {e}")
        
        logger.info(f"Collected {len(signals)} GitHub exposure signals")
        return signals
    
    def check_hibp_breaches(self) -> List[Dict]:
        """
        Check Have I Been Pwned for breach data ($3.50/month)
        Since you have the API key, let's use it!
        """
        signals = []
        
        try:
            from config.settings import config
            hibp_api_key = getattr(config, 'HIBP_API_KEY', None)
            
            if not hibp_api_key:
                logger.info("No HIBP API key configured, skipping breach checks")
                return signals
            
            logger.info("Checking Have I Been Pwned for breach data...")
            
            # Get companies to check
            try:
                companies = self.clay_client.query_table(
                    'company_universe',
                    {'checked_hibp': False}
                )
            except Exception as e:
                logger.error(f"Error querying companies for HIBP check: {e}")
                return signals
            
            if not companies:
                logger.info("No companies need HIBP checking")
                return signals
                
            if not isinstance(companies, list):
                try:
                    companies = list(companies) if companies else []
                except Exception:
                    logger.error("Invalid company data from Clay query")
                    return signals
            
            # Check up to 10 companies per run (HIBP rate limits)
            companies = companies[:10]
            logger.info(f"Checking {len(companies)} companies for HIBP breaches")
            
            company_updates = []
            
            for i, company in enumerate(companies):
                if not isinstance(company, dict):
                    continue
                    
                domain = company.get('domain')
                company_name = company.get('company_name', '')
                
                if not domain or not company_name:
                    continue
                
                logger.info(f"Checking HIBP for {company_name} ({domain}) [{i+1}/{len(companies)}]")
                
                try:
                    # Rate limit - HIBP allows 1 request every 1.5 seconds
                    time.sleep(1.6)
                    
                    # HIBP API call
                    response = self.session.get(
                        f'https://haveibeenpwned.com/api/v3/breaches',
                        params={'domain': domain},
                        headers={
                            'hibp-api-key': hibp_api_key,
                            'User-Agent': 'BTA-ThreatMonitor/1.0'
                        },
                        timeout=15
                    )
                    
                    if response.status_code == 404:
                        # No breaches found for this domain
                        logger.debug(f"No HIBP breaches found for {domain}")
                    elif response.status_code == 200:
                        try:
                            breaches = response.json()
                            if breaches:
                                # Found breaches for this domain
                                signal = {
                                    'company_name': company_name,
                                    'domain': domain,
                                    'signal_type': 'hibp_breach',
                                    'signal_date': datetime.utcnow().isoformat(),
                                    'signal_strength': 0.9,  # High priority
                                    'raw_data': {
                                        'breach_count': len(breaches),
                                        'recent_breaches': [b.get('Name', '') for b in breaches[:3]],
                                        'breach_details': breaches[:3]  # Keep first 3 for details
                                    },
                                    'source': 'haveibeenpwned'
                                }
                                signals.append(signal)
                                logger.warning(f"Found HIBP breaches for {company_name}: {len(breaches)} breaches")
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON from HIBP for {domain}")
                    elif response.status_code == 429:
                        logger.warning(f"HIBP rate limit hit, stopping batch")
                        break
                    else:
                        logger.warning(f"HIBP API returned {response.status_code} for {domain}")
                
                except requests.RequestException as e:
                    logger.error(f"Network error during HIBP check for {domain}: {e}")
                
                # Mark as checked
                company_updates.append({
                    'company_name': company_name,
                    'domain': domain,
                    'checked_hibp': True,
                    'last_checked_hibp': datetime.utcnow().isoformat()
                })
            
            # Update companies as checked
            if company_updates:
                try:
                    self.clay_client.bulk_upsert('company_universe', company_updates)
                    logger.info(f"Updated {len(company_updates)} companies as HIBP-checked")
                except Exception as e:
                    logger.error(f"Error updating HIBP check status: {e}")
        
        except Exception as e:
            logger.error(f"Unexpected error in HIBP check: {e}")
        
        logger.info(f"Collected {len(signals)} HIBP breach signals")
        return signals
    
    def check_shodan_exposures(self) -> List[Dict]:
        """
        Optional: Shodan monitoring ($59/month)
        Only use if you have API key
        """
        signals = []
        
        # Only run if Shodan key is configured
        if not getattr(self, 'shodan_api_key', None):
            return signals
        
        # Import shodan safely; if not installed, skip
        try:
            try:
                import shodan
            except Exception:
                logging.warning("shodan package not installed; skipping shodan checks")
                return signals
            
            api = shodan.Shodan(self.shodan_api_key)
            
            # Get companies to check
            companies = self.clay_client.query_table(
                'company_universe',
                {'checked_shodan': False}
            ) or []
            companies = companies[:5]  # Check 5 at a time
            
            for company in companies:
                if not isinstance(company, dict):
                    continue
                domain = company.get('domain')
                if not domain:
                    continue
                
                # Search for exposed services
                try:
                    results = api.search(f'hostname:{domain}')
                except Exception as e:
                    logging.error(f"Shodan API error for {domain}: {e}")
                    continue
                
                vulnerable_services = []
                for result in results.get('matches', []):
                    if result.get('vulns'):
                        vulnerable_services.append({
                            'port': result.get('port'),
                            'service': result.get('product', 'Unknown'),
                            'vulns': list(result.get('vulns', {}).keys())[:3]
                        })
                
                if vulnerable_services:
                    signal = {
                        'company_name': company.get('company_name', ''),
                        'domain': domain,
                        'signal_type': 'exposed_systems',
                        'signal_date': datetime.utcnow().isoformat(),
                        'signal_strength': 0.8,
                        'raw_data': {
                            'exposed_count': len(vulnerable_services),
                            'services': vulnerable_services
                        },
                        'source': 'shodan'
                    }
                    signals.append(signal)

        except Exception as e:
            logging.error(f"Shodan error: {e}")

        return signals
    
    def estimate_domain(self, company_name: str) -> str:
        """Estimate domain from company name"""
        import re
        clean_name = re.sub(r'[^\w\s]', '', company_name.lower())
        clean_name = re.sub(r'\s+(inc|llc|corp|corporation|ltd|limited|company|co)$', '', clean_name)
        clean_name = clean_name.replace(' ', '')
        return f"{clean_name}.com"
    
    def push_to_clay(self, signals: List[Dict]):
        """Push threat signals to Clay webhook in batches"""
        from config.settings import config
        
        if not config.CLAY_WEBHOOK_URL:
            print("Warning: No Clay webhook URL configured")
            return
        
        if not signals:
            print("No threat signals to send")
            return
        
        # Send data in smaller batches to avoid payload size limits
        batch_size = 50  # Reduced batch size for Clay webhook payload limits
        total_batches = (len(signals) + batch_size - 1) // batch_size
        
        print(f"Sending {len(signals)} threat signals in {total_batches} batches of {batch_size}")
        
        successful_batches = 0
        failed_batches = 0
        
        for i in range(0, len(signals), batch_size):
            batch = signals[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            # Prepare webhook payload for this batch
            webhook_data = {
                'event_type': 'threat_intelligence_collection',
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'free_darkweb_monitor',
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
                    'batch_threats': len(batch),
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
                    'raw_data': signal['raw_data'],  # Keep as dict, not JSON string
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
            # Prepare webhook request
            webhook_url = config.CLAY_WEBHOOK_URL
            payload = json.dumps(data, indent=2)
            
            # Set up headers
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'BTA-ThreatMonitor/1.0'
            }
            
            # Add webhook signature if secret is configured
            if config.CLAY_WEBHOOK_SECRET:
                signature = hmac.new(
                    config.CLAY_WEBHOOK_SECRET.encode(),
                    payload.encode(),
                    hashlib.sha256
                ).hexdigest()
                headers['X-Webhook-Signature'] = f'sha256={signature}'
            
            # Make the webhook request
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
        """Main entry point - replaces DarkOwl collection"""
        print("Starting free threat monitoring...")
        
        # Collect all threats
        all_signals = self.collect_all_threats()
        
        print(f"Found {len(all_signals)} threat signals")
        
        # Push to Clay
        self.push_to_clay(all_signals)
        
        print("Threat monitoring complete")
