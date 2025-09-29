import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

class ClayClient:
    def __init__(self, api_key: str, workspace: str):
        self.api_key = api_key
        self.workspace = workspace
        self.base_url = f"https://api.clay.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.rate_limiter = RateLimiter(calls=100, period=60)
    
    def get_table(self, table_name: str) -> Dict:
        """Get table schema and metadata"""
        self.rate_limiter.wait_if_needed()
        url = f"{self.base_url}/tables/{table_name}"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def add_row(self, table_name: str, data: Dict) -> Dict:
        """Add single row to table"""
        self.rate_limiter.wait_if_needed()
        url = f"{self.base_url}/tables/{table_name}/rows"
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()
    
    def bulk_upsert(self, table_name: str, rows: List[Dict], 
                    unique_key: str = 'domain') -> Dict:
        """Bulk upsert rows with deduplication"""
        self.rate_limiter.wait_if_needed()
        url = f"{self.base_url}/tables/{table_name}/bulk-upsert"
        payload = {
            "rows": rows,
            "unique_key": unique_key,
            "update_existing": True
        }
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()
    
    def query_table(self, table_name: str, filters: Dict) -> List[Dict]:
        """Query table with filters"""
        self.rate_limiter.wait_if_needed()
        url = f"{self.base_url}/tables/{table_name}/query"
        response = requests.post(url, headers=self.headers, json=filters)
        return response.json().get('rows', [])
    
    def trigger_webhook(self, webhook_url: str, data: Dict) -> bool:
        """Send data to Clay webhook"""
        try:
            response = requests.post(
                webhook_url,
                json=data,
                headers={"X-Clay-Signature": self.generate_signature(data)}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Webhook error: {e}")
            return False
    
    def generate_signature(self, data: Dict) -> str:
        """Generate webhook signature for security"""
        import hmac
        import hashlib
        
        message = json.dumps(data, sort_keys=True)
        signature = hmac.new(
            self.workspace.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def send_to_clay_for_company_creation(self, signal_data: Dict) -> Dict:
        """
        Send signal to Clay with enrichment instructions
        Aligned with existing webhook architecture
        """
        self.rate_limiter.wait_if_needed()
        
        # Extract or find domain
        domain = self.extract_domain(signal_data)
        if not domain:
            raise ValueError("Could not extract domain from signal data")
        
        # Prepare payload matching existing webhook structure
        payload = {
            "event_type": "signal_enrichment_request",
            "timestamp": datetime.utcnow().isoformat(),
            "source": "clay_client_enrichment",
            "data": {
                "companies": [{
                    "company_name": signal_data.get('company_name', ''),
                    "domain": domain,
                    "data_source": signal_data.get('source', 'unknown'),
                    "last_updated": datetime.utcnow().isoformat(),
                    "needs_enrichment": True
                }],
                "pain_signals": [{
                    "domain": domain,
                    "signal_type": signal_data['signal_type'],
                    "signal_date": signal_data.get('signal_date', datetime.utcnow().isoformat()),
                    "signal_strength": signal_data['signal_strength'],
                    "raw_data": signal_data.get('raw_data', {}),
                    "source": signal_data.get('source', 'unknown'),
                    "enrichment_priority": self.get_priority(signal_data['signal_type']),
                    "campaign_type": self.suggest_campaign(signal_data['signal_type'])
                }]
            }
        }
        
        # Send to Clay using existing webhook infrastructure
        from config.settings import config
        webhook_url = config.CLAY_WEBHOOK_URL
        
        if not webhook_url:
            raise ValueError("CLAY_WEBHOOK_URL not configured")
        
        try:
            response = requests.post(
                webhook_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Clay-Signature": self.generate_signature(payload)
                }
            )
            print(f"Webhook response status: {response.status_code}")
            print(f"Webhook response text: {response.text[:200]}...")
            
            if response.status_code == 200:
                try:
                    return response.json()
                except:
                    return {"status": "success", "message": "Webhook sent successfully"}
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            print(f"Error sending enrichment request: {e}")
            return {"error": str(e)}
    
    def extract_domain(self, signal_data: Dict) -> Optional[str]:
        """Extract domain from various signal types"""
        
        # For ransomware signals
        if 'raw_data' in signal_data and isinstance(signal_data['raw_data'], dict):
            if 'website' in signal_data['raw_data']:
                website = signal_data['raw_data']['website']
                if website:
                    return website.replace('www.', '').replace('http://', '').replace('https://', '').split('/')[0]
        
        # For breach signals
        if 'domain' in signal_data:
            return signal_data['domain']
        
        # Try to extract from company name (fallback)
        company_name = signal_data.get('company_name', '')
        if company_name:
            # Simple domain estimation (matches existing pattern)
            clean_name = company_name.lower().replace(' ', '').replace('inc', '').replace('llc', '').replace('corp', '')
            return f"{clean_name}.com"
        
        return None
    
    def get_priority(self, signal_type: str) -> float:
        """Get enrichment priority based on signal type"""
        priorities = {
            'active_ransomware': 1.0,
            'post_breach': 0.9,
            'insurance_coverage_issue': 0.85,
            'executive_vacancy_critical': 0.8,
            'missing_mdr': 0.75,
            'missing_siem': 0.7,
            'dark_web_mention': 0.65,
            'skills_gap_critical': 0.6
        }
        return priorities.get(signal_type, 0.5)
    
    def suggest_campaign(self, signal_type: str) -> str:
        """Suggest campaign based on signal type"""
        campaigns = {
            'active_ransomware': 'emergency_ransomware',
            'post_breach': 'breach_recovery',
            'dark_web_mention': 'dark_web_alert',
            'missing_mdr': 'dwell_time_alert',
            'missing_siem': 'siem_gap_analysis',
            'skills_gap_critical': 'skills_gap_tax',
            'insurance_coverage_issue': 'insurance_gap_analysis',
            'executive_vacancy_critical': 'leadership_gap_alert'
        }
        return campaigns.get(signal_type, 'general_outreach')

class RateLimiter:
    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period
        self.timestamps = []
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()
        # Remove timestamps outside the period
        self.timestamps = [t for t in self.timestamps if now - t < self.period]
        
        if len(self.timestamps) >= self.calls:
            sleep_time = self.period - (now - self.timestamps[0]) + 0.1
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.timestamps.append(time.time())