import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import json
import os
import hashlib
from typing import List, Dict

class BreachCollector:
    def __init__(self, clay_client):
        self.clay_client = clay_client
        self.sources = {
            'california_ag': 'https://oag.ca.gov/privacy/databreach/list',
            'hhs_hipaa': 'https://ocrportal.hhs.gov/ocr/breach/breach_report.jsf',
            'sec_edgar': 'https://www.sec.gov/edgar/searchedgar/companysearch.html'
        }
        self.sent_data_file = 'data/sent_breach_hashes.json'
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Ensure data directory exists for tracking sent data"""
        data_dir = os.path.dirname(self.sent_data_file)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir)
    
    def _get_breach_hash(self, breach: Dict) -> str:
        """Create unique hash for breach record"""
        # Create hash from company name, breach date, and source
        key_data = f"{breach['company_name']}|{breach['breach_date']}|{breach['source']}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _load_sent_hashes(self) -> set:
        """Load previously sent breach hashes"""
        try:
            if os.path.exists(self.sent_data_file):
                with open(self.sent_data_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('sent_hashes', []))
            return set()
        except Exception as e:
            print(f"Error loading sent hashes: {e}")
            return set()
    
    def _save_sent_hashes(self, hashes: set):
        """Save sent breach hashes to file"""
        try:
            data = {
                'sent_hashes': list(hashes),
                'last_updated': datetime.now().isoformat(),
                'total_sent': len(hashes)
            }
            with open(self.sent_data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving sent hashes: {e}")
    
    def filter_new_breaches(self, breaches: List[Dict]) -> List[Dict]:
        """Filter out breaches that have already been sent"""
        if not breaches:
            return []
        
        print(f"Checking {len(breaches)} breaches for duplicates...")
        
        # Load previously sent hashes
        sent_hashes = self._load_sent_hashes()
        print(f"Found {len(sent_hashes)} previously sent breach records")
        
        # Filter out duplicates
        new_breaches = []
        for breach in breaches:
            breach_hash = self._get_breach_hash(breach)
            if breach_hash not in sent_hashes:
                new_breaches.append(breach)
        
        print(f"Found {len(new_breaches)} new breaches (filtered out {len(breaches) - len(new_breaches)} duplicates)")
        return new_breaches
    
    def mark_breaches_as_sent(self, breaches: List[Dict]):
        """Mark breaches as sent to avoid future duplicates"""
        if not breaches:
            return
        
        # Load existing hashes
        sent_hashes = self._load_sent_hashes()
        
        # Add new hashes
        for breach in breaches:
            breach_hash = self._get_breach_hash(breach)
            sent_hashes.add(breach_hash)
        
        # Save updated hashes
        self._save_sent_hashes(sent_hashes)
        print(f"Marked {len(breaches)} breaches as sent")
    
    def collect_ca_breaches(self) -> List[Dict]:
        """Scrape California AG breach notifications"""
        breaches = []
        
        try:
            response = requests.get(self.sources['california_ag'])
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the correct breach table - updated selector based on analysis
            breach_table = soup.find('table', {'class': lambda x: x and 'views-table' in x})
            
            if breach_table:
                rows = breach_table.find_all('tr')[1:]  # Skip header
                print(f"Found {len(rows)} breach records in CA AG table")
                
                for row in rows:
                    breach = self.parse_breach_row(row)
                    if breach:
                        breaches.append(breach)
            else:
                print("Could not find breach table in CA AG website")
        
        except Exception as e:
            print(f"Error collecting CA breaches: {e}")
        
        return breaches
    
    def parse_breach_row(self, row) -> Dict:
        """Parse individual breach row"""
        cells = row.find_all('td')
        if len(cells) >= 3:
            company_name = cells[0].text.strip()
            breach_date = cells[1].text.strip()
            notice_date = cells[2].text.strip()
            
            # Skip empty or invalid rows
            if not company_name or company_name.lower() in ['', 'organization name']:
                return None
            
            return {
                'company_name': company_name,
                'breach_date': self.parse_date(breach_date),
                'notice_date': self.parse_date(notice_date),
                'source': 'california_ag',
                'signal_type': 'post_breach',
                'signal_strength': self.calculate_breach_recency_score(breach_date)
            }
        return None
    
    def parse_date(self, date_str: str) -> str:
        """Parse various date formats"""
        formats = ['%m/%d/%Y', '%Y-%m-%d', '%B %d, %Y']
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).isoformat()
            except:
                continue
        return date_str
    
    def calculate_breach_recency_score(self, breach_date_str: str) -> float:
        """Calculate signal strength based on breach recency"""
        try:
            breach_date = datetime.fromisoformat(self.parse_date(breach_date_str))
            days_ago = (datetime.now() - breach_date).days
            
            if days_ago <= 30:
                return 1.0  # Maximum urgency
            elif days_ago <= 90:
                return 0.8
            elif days_ago <= 180:
                return 0.6
            elif days_ago <= 365:
                return 0.4
            else:
                return 0.2
        except:
            return 0.5  # Default medium score
    
    def collect_hhs_breaches(self) -> List[Dict]:
        """Collect HIPAA breach reports"""
        breaches = []
        
        try:
            # First, get the page to establish session
            session = requests.Session()
            initial_response = session.get('https://ocrportal.hhs.gov/ocr/breach/breach_report.jsf')
            soup = BeautifulSoup(initial_response.content, 'html.parser')
            
            # Look for existing table data (some sites show initial data)
            tables = soup.find_all('table')
            data_found = False
            
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) > 3:  # More than just headers
                    print(f"Found HHS table with {len(rows)} rows")
                    for row in rows[1:]:  # Skip header
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 3:
                            cell_text = [cell.get_text().strip() for cell in cells]
                            # Look for valid breach data
                            if any(cell_text) and not all(cell.lower() in ['', 'loading...', 'no data'] for cell in cell_text):
                                breach = self.parse_hhs_row(cell_text)
                                if breach:
                                    breaches.append(breach)
                                    data_found = True
                    
                    if data_found:
                        break
            
            if not data_found:
                print("No immediate HHS data found in tables, may require JavaScript/AJAX")
                
        except Exception as e:
            print(f"Error collecting HHS breaches: {e}")
        
        return breaches
    
    def parse_hhs_row(self, cells: List[str]) -> Dict:
        """Parse HHS breach row from cell text"""
        try:
            if len(cells) >= 3:
                company_name = cells[0]
                # Skip empty or header rows
                if not company_name or company_name.lower() in ['name of covered entity', 'loading...', '']:
                    return None
                
                return {
                    'company_name': company_name,
                    'breach_date': self.parse_date(cells[1]) if len(cells) > 1 else '',
                    'affected_count': self.parse_number(cells[2]) if len(cells) > 2 else 0,
                    'breach_type': cells[3] if len(cells) > 3 else 'Unknown',
                    'location': cells[4] if len(cells) > 4 else 'Unknown',
                    'source': 'hhs_hipaa',
                    'signal_type': 'healthcare_breach',
                    'signal_strength': 0.8  # High severity for healthcare breaches
                }
        except Exception as e:
            print(f"Error parsing HHS row: {e}")
        return None
    
    def parse_number(self, text: str) -> int:
        """Extract number from text"""
        import re
        numbers = re.findall(r'\d+', text.replace(',', ''))
        return int(numbers[0]) if numbers else 0
    
    def calculate_hipaa_severity(self, breach: Dict) -> float:
        """Calculate HIPAA breach severity score"""
        score = 0.5  # Base score
        
        # Increase for large breaches
        affected = breach.get('Individuals_Affected', 0)
        if affected > 10000:
            score += 0.3
        elif affected > 5000:
            score += 0.2
        elif affected > 1000:
            score += 0.1
        
        # Increase for recent breaches
        days_ago = (datetime.now() - datetime.fromisoformat(breach['Breach_Submission_Date'])).days
        if days_ago <= 30:
            score += 0.2
        elif days_ago <= 90:
            score += 0.1
        
        return min(score, 1.0)
    
    def push_to_clay(self, breaches: List[Dict]):
        """Push breach data to Clay webhook in batches"""
        from config.settings import config
        
        if not config.CLAY_WEBHOOK_URL:
            print("Warning: No Clay webhook URL configured")
            return
        
        if not breaches:
            print("No breach data to send")
            return
        
        # Send data in smaller batches to avoid payload size limits
        batch_size = 100  # Clay webhook payload limit consideration
        total_batches = (len(breaches) + batch_size - 1) // batch_size
        
        print(f"Sending {len(breaches)} breaches in {total_batches} batches of {batch_size}")
        
        successful_batches = 0
        failed_batches = 0
        
        for i in range(0, len(breaches), batch_size):
            batch = breaches[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            # Prepare webhook payload for this batch
            webhook_data = {
                'event_type': 'breach_data_collection',
                'timestamp': datetime.now().isoformat(),
                'source': 'breach_collector',
                'batch_info': {
                    'batch_number': batch_num,
                    'total_batches': total_batches,
                    'batch_size': len(batch),
                    'total_records': len(breaches)
                },
                'data': {
                    'companies': [],
                    'pain_signals': []
                },
                'summary': {
                    'batch_breaches': len(batch),
                    'sources': list(set([b['source'] for b in batch]))
                }
            }
            
            for breach in batch:
                # Prepare company record
                domain = self.estimate_domain(breach['company_name'])
                company = {
                    'company_name': breach['company_name'],
                    'domain': domain,
                    'data_source': breach['source'],
                    'last_updated': datetime.now().isoformat()
                }
                webhook_data['data']['companies'].append(company)
                
                # Prepare signal record
                signal = {
                    'domain': domain,
                    'signal_type': breach['signal_type'],
                    'signal_date': breach['breach_date'],
                    'signal_strength': breach['signal_strength'],
                    'raw_data': breach,
                    'source': breach['source']
                }
                webhook_data['data']['pain_signals'].append(signal)
            
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
        import json
        import hashlib
        import hmac
        
        try:
            # Prepare webhook request
            webhook_url = config.CLAY_WEBHOOK_URL
            payload = json.dumps(data, indent=2)
            
            # Set up headers
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'BTA-BreachCollector/1.0'
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
            response = requests.post(
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
    
    def estimate_domain(self, company_name: str) -> str:
        """Estimate domain from company name"""
        # Clean company name
        clean_name = re.sub(r'[^\w\s]', '', company_name.lower())
        clean_name = re.sub(r'\s+(inc|llc|corp|corporation|ltd|limited|company|co)$', '', clean_name)
        clean_name = clean_name.replace(' ', '')
        
        return f"{clean_name}.com"
    
    def run_collection(self):
        """Main collection orchestration with duplicate detection"""
        print("Starting breach collection...")
        
        # Collect from all sources
        all_breaches = []
        all_breaches.extend(self.collect_ca_breaches())
        all_breaches.extend(self.collect_hhs_breaches())
        
        print(f"Collected {len(all_breaches)} total breaches")
        
        # Filter out duplicates
        new_breaches = self.filter_new_breaches(all_breaches)
        
        if new_breaches:
            # Push only new data to Clay
            self.push_to_clay(new_breaches)
            
            # Mark as sent to prevent future duplicates
            self.mark_breaches_as_sent(new_breaches)
            
            print(f"Sent {len(new_breaches)} new breach records to Clay")
        else:
            print("No new breach data to send")
        
        print("Breach collection complete")
