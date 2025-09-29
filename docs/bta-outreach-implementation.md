# Blue Team Alpha: Complete Implementation Guide
## Clay + n8n + Python Integration System

---

## System Architecture Overview

```
[DATA SOURCES] → [n8n Collectors] → [Clay Tables] → [Python Scoring] → [Clay Enrichment] → [Python Campaign] → [Clay Webhook] → [Outbound Sequences]
```

---

## Phase 1: Foundation Setup (Days 1-3)

### Step 1: Create Clay Infrastructure

#### 1.1 Create Master Tables in Clay

```sql
-- Table 1: Company Universe
CREATE TABLE company_universe (
    company_name TEXT,
    domain TEXT PRIMARY KEY,
    industry TEXT,
    employee_count INT,
    location TEXT,
    linkedin_url TEXT,
    last_updated TIMESTAMP,
    data_source TEXT
)

-- Table 2: Pain Signals
CREATE TABLE pain_signals (
    signal_id SERIAL PRIMARY KEY,
    domain TEXT,
    signal_type TEXT, -- 'breach', 'vacancy', 'dark_web', 'insurance'
    signal_date DATE,
    signal_strength FLOAT,
    raw_data JSON,
    source TEXT
)

-- Table 3: Scored Prospects
CREATE TABLE scored_prospects (
    domain TEXT PRIMARY KEY,
    pain_score FLOAT,
    segment TEXT,
    edp_primary TEXT,
    edp_data JSON,
    ready_for_outreach BOOLEAN,
    campaign_type TEXT
)

-- Table 4: Outreach Queue
CREATE TABLE outreach_queue (
    queue_id SERIAL PRIMARY KEY,
    domain TEXT,
    contact_email TEXT,
    contact_name TEXT,
    contact_title TEXT,
    campaign_type TEXT,
    message_personalized TEXT,
    scheduled_send TIMESTAMP,
    status TEXT
)
```

#### 1.2 Set Up Clay Webhooks

1. Go to Clay Settings → Integrations → Webhooks
2. Create webhook endpoint: `https://your-clay-workspace.clay.com/webhook/outreach`
3. Note the webhook URL and secret key
4. Create return webhook for Python: `https://your-server.com/clay-callback`

---

### Step 2: Configure n8n Workflows

#### 2.1 Install n8n (if not already installed)

```bash
# Using Docker
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n

# Or using npm
npm install n8n -g
n8n start
```

#### 2.2 Create Breach Monitor Workflow

```json
{
  "name": "Breach Monitor",
  "nodes": [
    {
      "name": "Schedule",
      "type": "n8n-nodes-base.cron",
      "parameters": {
        "cronExpression": "0 6 * * *"  // Daily at 6 AM
      }
    },
    {
      "name": "Fetch CA Breaches",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://oag.ca.gov/privacy/databreach/list",
        "method": "GET",
        "responseFormat": "string"
      }
    },
    {
      "name": "Parse HTML",
      "type": "n8n-nodes-base.html",
      "parameters": {
        "extractionValues": {
          "values": [
            {
              "key": "company",
              "cssSelector": ".breach-company",
              "returnValue": "text"
            },
            {
              "key": "date",
              "cssSelector": ".breach-date",
              "returnValue": "text"
            }
          ]
        }
      }
    },
    {
      "name": "Send to Clay",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "httpMethod": "POST",
        "path": "https://api.clay.com/v1/tables/company_universe/rows",
        "authentication": "headerAuth",
        "headerAuth": {
          "name": "Authorization",
          "value": "Bearer YOUR_CLAY_API_KEY"
        }
      }
    }
  ]
}
```

#### 2.3 Create Job Posting Monitor

```json
{
  "name": "Security Vacancy Tracker",
  "nodes": [
    {
      "name": "Daily Trigger",
      "type": "n8n-nodes-base.cron",
      "parameters": {
        "cronExpression": "0 8 * * *"
      }
    },
    {
      "name": "Search Indeed",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://www.indeed.com/jobs",
        "queryParameters": {
          "q": "CISO OR 'Chief Information Security Officer' OR 'Security Director'",
          "l": "United States",
          "fromage": "30",  // Posted in last 30 days
          "limit": "50"
        }
      }
    },
    {
      "name": "Extract Companies",
      "type": "n8n-nodes-base.itemLists",
      "parameters": {
        "operation": "extractFieldValues",
        "fields": ["company", "job_title", "posted_date"]
      }
    },
    {
      "name": "Check Days Open",
      "type": "n8n-nodes-base.function",
      "parameters": {
        "functionCode": `
          const items = $input.all();
          return items.map(item => {
            const postedDate = new Date(item.json.posted_date);
            const today = new Date();
            const daysOpen = Math.floor((today - postedDate) / (1000 * 60 * 60 * 24));
            
            if (daysOpen > 60) {
              item.json.signal_strength = 0.9;
              item.json.signal_type = 'skills_gap_critical';
            } else if (daysOpen > 30) {
              item.json.signal_strength = 0.7;
              item.json.signal_type = 'skills_gap_moderate';
            }
            
            item.json.days_open = daysOpen;
            return item;
          });
        `
      }
    },
    {
      "name": "Push to Clay",
      "type": "n8n-nodes-base.clay",
      "parameters": {
        "operation": "upsert",
        "table": "pain_signals"
      }
    }
  ]
}
```

---

### Step 3: Set Up Python Processing Environment

#### 3.1 Create Project Structure

```bash
mkdir blue-team-alpha-agent
cd blue-team-alpha-agent

# Create directory structure
mkdir -p {src,data,logs,config,scripts}

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 3.2 Create requirements.txt

```txt
# Core
pandas==2.0.3
numpy==1.24.3
requests==2.31.0
python-dotenv==1.0.0

# APIs
clay-python==0.1.0  # Custom wrapper we'll build
aiohttp==3.8.5
asyncio==3.4.3

# Data Processing
beautifulsoup4==4.12.2
lxml==4.9.3
python-dateutil==2.8.2

# Scheduling
schedule==1.2.0
celery==5.3.1
redis==4.6.0

# Web Framework
fastapi==0.103.0
uvicorn==0.23.2
pydantic==2.3.0

# Database
psycopg2-binary==2.9.7
sqlalchemy==2.0.20
alembic==1.11.3

# Monitoring
sentry-sdk==1.30.0
prometheus-client==0.17.1

# Testing
pytest==7.4.0
pytest-asyncio==0.21.1
```

#### 3.3 Create Configuration File

```python
# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Clay Configuration
    CLAY_API_KEY = os.getenv('CLAY_API_KEY')
    CLAY_WORKSPACE = os.getenv('CLAY_WORKSPACE')
    CLAY_WEBHOOK_URL = os.getenv('CLAY_WEBHOOK_URL')
    CLAY_WEBHOOK_SECRET = os.getenv('CLAY_WEBHOOK_SECRET')
    
    # n8n Configuration
    N8N_URL = os.getenv('N8N_URL', 'http://localhost:5678')
    N8N_API_KEY = os.getenv('N8N_API_KEY')
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/bta')
    
    # Redis (for queuing)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # API Keys for Data Sources
    DARKOWL_API_KEY = os.getenv('DARKOWL_API_KEY')
    BITSIGHT_API_KEY = os.getenv('BITSIGHT_API_KEY')
    WAPPALYZER_API_KEY = os.getenv('WAPPALYZER_API_KEY')
    
    # Scoring Thresholds
    MIN_PAIN_SCORE = 70  # Minimum score to qualify for outreach
    POST_BREACH_THRESHOLD = 90
    SKILLS_GAP_THRESHOLD = 75
    INSURANCE_THRESHOLD = 80
    
    # Rate Limits
    CLAY_RATE_LIMIT = 100  # requests per minute
    OUTREACH_DAILY_LIMIT = 500
    
    # Timing
    BUSINESS_HOURS_START = 9  # 9 AM
    BUSINESS_HOURS_END = 17  # 5 PM
    TIMEZONE = 'America/Chicago'

config = Config()
```

---

## Phase 2: Data Collection Implementation (Days 4-7)

### Step 4: Build Clay API Wrapper

```python
# src/clay_client.py
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
```

### Step 5: Implement Data Collectors

#### 5.1 Breach Data Collector

```python
# src/collectors/breach_collector.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
from typing import List, Dict

class BreachCollector:
    def __init__(self, clay_client):
        self.clay_client = clay_client
        self.sources = {
            'california_ag': 'https://oag.ca.gov/privacy/databreach/list',
            'hhs_hipaa': 'https://ocrportal.hhs.gov/ocr/breach/breach_report.jsf',
            'sec_edgar': 'https://www.sec.gov/edgar/searchedgar/companysearch.html'
        }
    
    def collect_ca_breaches(self) -> List[Dict]:
        """Scrape California AG breach notifications"""
        breaches = []
        
        try:
            response = requests.get(self.sources['california_ag'])
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find breach table
            breach_table = soup.find('table', {'class': 'breach-list'})
            if not breach_table:
                # Alternative parsing for different page structure
                breach_divs = soup.find_all('div', {'class': 'breach-item'})
                for div in breach_divs:
                    breach = self.parse_breach_div(div)
                    if breach:
                        breaches.append(breach)
            else:
                rows = breach_table.find_all('tr')[1:]  # Skip header
                for row in rows:
                    breach = self.parse_breach_row(row)
                    if breach:
                        breaches.append(breach)
        
        except Exception as e:
            print(f"Error collecting CA breaches: {e}")
        
        return breaches
    
    def parse_breach_row(self, row) -> Dict:
        """Parse individual breach row"""
        cells = row.find_all('td')
        if len(cells) >= 3:
            return {
                'company_name': cells[0].text.strip(),
                'breach_date': self.parse_date(cells[1].text.strip()),
                'notice_date': self.parse_date(cells[2].text.strip()),
                'source': 'california_ag',
                'signal_type': 'post_breach',
                'signal_strength': self.calculate_breach_recency_score(cells[1].text.strip())
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
        
        # Build API request for HHS breach portal
        params = {
            'start': 0,
            'length': 100,
            'draw': 1,
            'search[value]': '',
            'order[0][column]': 5,  # Order by breach date
            'order[0][dir]': 'desc'
        }
        
        try:
            response = requests.post(
                'https://ocrportal.hhs.gov/ocr/breach/breach_report.jsf',
                data=params
            )
            data = response.json()
            
            for item in data.get('data', []):
                breach = {
                    'company_name': item['Name_of_Covered_Entity'],
                    'breach_date': item['Breach_Submission_Date'],
                    'affected_count': int(item['Individuals_Affected']),
                    'breach_type': item['Type_of_Breach'],
                    'location': item['State'],
                    'source': 'hhs_hipaa',
                    'signal_type': 'healthcare_breach',
                    'signal_strength': self.calculate_hipaa_severity(item)
                }
                breaches.append(breach)
        
        except Exception as e:
            print(f"Error collecting HHS breaches: {e}")
        
        return breaches
    
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
        """Push breach data to Clay tables"""
        # First, add to company universe
        companies = []
        signals = []
        
        for breach in breaches:
            # Prepare company record
            company = {
                'company_name': breach['company_name'],
                'domain': self.estimate_domain(breach['company_name']),
                'data_source': breach['source'],
                'last_updated': datetime.now().isoformat()
            }
            companies.append(company)
            
            # Prepare signal record
            signal = {
                'domain': company['domain'],
                'signal_type': breach['signal_type'],
                'signal_date': breach['breach_date'],
                'signal_strength': breach['signal_strength'],
                'raw_data': breach,
                'source': breach['source']
            }
            signals.append(signal)
        
        # Bulk upsert to Clay
        if companies:
            self.clay_client.bulk_upsert('company_universe', companies)
        if signals:
            self.clay_client.bulk_upsert('pain_signals', signals)
    
    def estimate_domain(self, company_name: str) -> str:
        """Estimate domain from company name"""
        # Clean company name
        clean_name = re.sub(r'[^\w\s]', '', company_name.lower())
        clean_name = re.sub(r'\s+(inc|llc|corp|corporation|ltd|limited|company|co)$', '', clean_name)
        clean_name = clean_name.replace(' ', '')
        
        return f"{clean_name}.com"
    
    def run_collection(self):
        """Main collection orchestration"""
        print("Starting breach collection...")
        
        # Collect from all sources
        all_breaches = []
        all_breaches.extend(self.collect_ca_breaches())
        all_breaches.extend(self.collect_hhs_breaches())
        
        print(f"Collected {len(all_breaches)} total breaches")
        
        # Push to Clay
        self.push_to_clay(all_breaches)
        
        print("Breach collection complete")
```

#### 5.2 Job Posting Collector

```python
# src/collectors/job_collector.py
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import json

class JobPostingCollector:
    def __init__(self, clay_client):
        self.clay_client = clay_client
        self.security_titles = [
            'CISO', 'Chief Information Security Officer',
            'Security Director', 'Director of Security',
            'Security Manager', 'SOC Manager',
            'Security Analyst', 'Security Engineer',
            'Threat Hunter', 'Incident Response'
        ]
    
    def collect_indeed_jobs(self) -> List[Dict]:
        """Collect security job postings from Indeed"""
        jobs = []
        
        for title in self.security_titles:
            try:
                # Use Indeed's public job search
                params = {
                    'q': title,
                    'l': 'United States',
                    'fromage': '30',  # Last 30 days
                    'limit': 50,
                    'format': 'json'
                }
                
                # Note: In production, use Indeed API or scraping service
                response = self.search_indeed(params)
                
                for job in response:
                    job_data = self.process_job_posting(job)
                    if job_data:
                        jobs.append(job_data)
            
            except Exception as e:
                print(f"Error collecting Indeed jobs for {title}: {e}")
        
        return jobs
    
    def process_job_posting(self, job: Dict) -> Dict:
        """Process individual job posting"""
        posted_date = job.get('date', '')
        days_open = self.calculate_days_open(posted_date)
        
        return {
            'company_name': job.get('company', ''),
            'job_title': job.get('jobtitle', ''),
            'location': job.get('formattedLocation', ''),
            'posted_date': posted_date,
            'days_open': days_open,
            'signal_type': self.categorize_vacancy_signal(days_open, job.get('jobtitle', '')),
            'signal_strength': self.calculate_vacancy_score(days_open, job.get('jobtitle', '')),
            'source': 'indeed',
            'url': job.get('url', '')
        }
    
    def calculate_days_open(self, posted_date: str) -> int:
        """Calculate how many days job has been open"""
        try:
            # Parse Indeed's relative dates
            if 'today' in posted_date.lower():
                return 0
            elif 'yesterday' in posted_date.lower():
                return 1
            elif 'days ago' in posted_date:
                days = int(posted_date.split()[0])
                return days
            else:
                # Try to parse actual date
                post_date = datetime.strptime(posted_date, '%Y-%m-%d')
                return (datetime.now() - post_date).days
        except:
            return 0
    
    def categorize_vacancy_signal(self, days_open: int, title: str) -> str:
        """Categorize vacancy signal type"""
        is_executive = any(term in title.upper() for term in ['CISO', 'CHIEF', 'DIRECTOR'])
        
        if days_open > 60:
            if is_executive:
                return 'executive_vacancy_critical'
            return 'skills_gap_critical'
        elif days_open > 30:
            if is_executive:
                return 'executive_vacancy_moderate'
            return 'skills_gap_moderate'
        else:
            return 'recent_posting'
    
    def calculate_vacancy_score(self, days_open: int, title: str) -> float:
        """Calculate vacancy signal strength"""
        base_score = 0.3
        
        # Increase for longer vacancies
        if days_open > 90:
            base_score += 0.4
        elif days_open > 60:
            base_score += 0.3
        elif days_open > 30:
            base_score += 0.2
        
        # Increase for executive positions
        if any(term in title.upper() for term in ['CISO', 'CHIEF', 'DIRECTOR']):
            base_score += 0.2
        
        return min(base_score, 1.0)
    
    def collect_linkedin_jobs(self) -> List[Dict]:
        """Collect from LinkedIn (requires Sales Navigator API)"""
        # Implementation depends on LinkedIn API access
        # This is a placeholder for the structure
        jobs = []
        
        try:
            # LinkedIn API call would go here
            pass
        except Exception as e:
            print(f"LinkedIn collection error: {e}")
        
        return jobs
    
    def push_to_clay(self, jobs: List[Dict]):
        """Push job posting data to Clay"""
        companies = []
        signals = []
        
        for job in jobs:
            # Create company record
            domain = self.estimate_domain(job['company_name'])
            
            company = {
                'company_name': job['company_name'],
                'domain': domain,
                'location': job['location'],
                'data_source': 'job_postings',
                'last_updated': datetime.now().isoformat()
            }
            companies.append(company)
            
            # Create signal record
            signal = {
                'domain': domain,
                'signal_type': job['signal_type'],
                'signal_date': datetime.now().isoformat(),
                'signal_strength': job['signal_strength'],
                'raw_data': job,
                'source': job['source']
            }
            signals.append(signal)
        
        # Bulk upsert
        if companies:
            self.clay_client.bulk_upsert('company_universe', companies)
        if signals:
            self.clay_client.bulk_upsert('pain_signals', signals)
    
    def estimate_domain(self, company_name: str) -> str:
        """Estimate domain from company name"""
        import re
        clean_name = re.sub(r'[^\w\s]', '', company_name.lower())
        clean_name = re.sub(r'\s+(inc|llc|corp|corporation|ltd|limited|company|co)$', '', clean_name)
        clean_name = clean_name.replace(' ', '')
        return f"{clean_name}.com"
```

---

## Phase 3: Scoring & Segmentation Engine (Days 8-10)

### Step 6: Build EDP Scoring System

```python
# src/scoring/edp_scorer.py
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
```

### Step 7: Implement Campaign Generator

```python
# src/campaigns/campaign_generator.py
from datetime import datetime, timedelta
from typing import Dict, List
import json

class CampaignGenerator:
    def __init__(self, clay_client):
        self.clay_client = clay_client
        self.templates = self.load_templates()
    
    def load_templates(self) -> Dict:
        """Load PVP templates"""
        return {
            'dark_web': {
                'subject': '[COMPANY] credentials found on Russian forum',
                'body': """Hi [NAME],

Your domain credentials were posted on a Russian-language forum [DAYS_AGO] days ago. 
The package includes [CREDENTIAL_COUNT] employee emails with passwords, including [ADMIN_COUNT] admin accounts.

The seller claims to have VPN access and is asking $[PRICE]. Based on the timestamp, 
they've been inside your network for at least [DWELL_DAYS] days.

Most victims don't discover breaches for 277 days. You have hours, maybe days, before escalation.

Reply REPORT for the full threat brief.

[SIGNATURE]"""
            },
            'insurance': {
                'subject': '[INSURER] denied 3 manufacturers cyber coverage last month',
                'body': """Hi [NAME],

[INSURER] just denied cyber insurance renewals to three manufacturers in [STATE]. 
All were your size. The reason? No 24/7 threat detection.

Your renewal is in [RENEWAL_MONTHS] months. The new requirements:
- Continuous monitoring (not just EDR)
- Sub-30 minute response times documented
- Threat hunting capabilities proven

Without coverage, your board assumes personal liability for any breach.

Reply REQUIREMENTS for the new underwriting checklist.

[SIGNATURE]"""
            },
            'dwell_time': {
                'subject': 'Attackers spend 277 days in networks like yours',
                'body': """Hi [NAME],

The average attacker dwells in [INDUSTRY] networks for 277 days before detection. 
That's 9 months of stealing IP, installing backdoors, and mapping systems.

Here's what happens during those 277 days:
- Days 1-30: Initial access, reconnaissance
- Days 31-90: Privilege escalation, lateral movement
- Days 91-180: Data identification and staging
- Days 181-277: Exfiltration and monetization

We detect and contain in under 15 minutes. The difference? Ex-NSA operators who think like attackers.

Reply TIMELINE to see where you likely are in this cycle.

[SIGNATURE]"""
            },
            'after_hours': {
                'subject': 'Your security team sleeps 128 hours per week',
                'body': """Hi [NAME],

Quick question - who's watching your network at 2 AM on Sunday?

76% of ransomware attacks happen outside business hours. For [COMPANY], 
that's [UNCOVERED_HOURS] hours per week of vulnerability.

Last weekend alone, we stopped 3 ransomware attacks for clients between midnight and 6 AM. 
The attackers know when you're not watching.

Your competitors using 24/7 MDR have 8,760 hours of coverage. You have 2,080.

Reply COVERAGE to see your vulnerability windows.

[SIGNATURE]"""
            },
            'skills_gap': {
                'subject': 'Your [ROLE] position has been open for [DAYS] days',
                'body': """Hi [NAME],

I noticed your [ROLE] position has been posted for [DAYS] days. 
The average time to fill a senior security role is now 6 months.

While that position sits empty, you're facing a $1.76M increase in breach risk 
(IBM Cost of a Breach Report 2024).

Instead of waiting 6 more months and paying $[SALARY]K + benefits, 
you could have nation-state level security expertise active tomorrow.

Our ex-NSA and DoD operators provide immediate 24/7 coverage while you continue your search.

Reply TEAM to learn how we can cover you starting Monday.

[SIGNATURE]"""
            }
        }
    
    def generate_campaign(self, company: Dict, score_data: Dict) -> Dict:
        """Generate personalized campaign for company"""
        # Select template based on primary EDP
        template_key = self.select_template(score_data['primary_edp'])
        template = self.templates[template_key]
        
        # Get contact information
        contacts = self.find_contacts(company['domain'])
        
        # Personalize for each contact
        campaigns = []
        for contact in contacts[:3]:  # Max 3 contacts per company
            personalized = self.personalize_message(
                template,
                company,
                contact,
                score_data
            )
            
            campaign = {
                'domain': company['domain'],
                'contact_email': contact['email'],
                'contact_name': contact['name'],
                'contact_title': contact['title'],
                'campaign_type': template_key,
                'subject': personalized['subject'],
                'message_personalized': personalized['body'],
                'scheduled_send': self.calculate_send_time(score_data),
                'segment': score_data['segment'],
                'pain_score': score_data['pain_score'],
                'status': 'queued'
            }
            campaigns.append(campaign)
        
        return campaigns
    
    def select_template(self, primary_edp: str) -> str:
        """Select best template for EDP"""
        mapping = {
            'dwell_time': 'dwell_time',
            'skills_gap': 'skills_gap',
            'after_hours': 'after_hours',
            'insurance': 'insurance',
            'breach_cost': 'dwell_time'  # Use dwell as default
        }
        return mapping.get(primary_edp, 'dwell_time')
    
    def personalize_message(self, template: Dict, company: Dict, 
                           contact: Dict, score_data: Dict) -> Dict:
        """Personalize template with company data"""
        # Prepare replacements
        replacements = {
            '[COMPANY]': company.get('company_name', ''),
            '[NAME]': contact.get('first_name', 'there'),
            '[ROLE]': 'CISO',
            '[DAYS]': '67',
            '[INDUSTRY]': company.get('industry', 'your industry'),
            '[STATE]': company.get('state', 'your state'),
            '[SALARY]': '275',
            '[UNCOVERED_HOURS]': '128',
            '[INSURER]': 'Chubb',
            '[RENEWAL_MONTHS]': '3',
            '[DAYS_AGO]': '3',
            '[CREDENTIAL_COUNT]': '47',
            '[ADMIN_COUNT]': '3',
            '[PRICE]': '4,500',
            '[DWELL_DAYS]': '11',
            '[SIGNATURE]': self.get_signature()
        }
        
        # Apply replacements
        subject = template['subject']
        body = template['body']
        
        for key, value in replacements.items():
            subject = subject.replace(key, str(value))
            body = body.replace(key, str(value))
        
        return {
            'subject': subject,
            'body': body
        }
    
    def find_contacts(self, domain: str) -> List[Dict]:
        """Find contacts for domain using Clay enrichment"""
        # This triggers Clay's contact enrichment
        contacts = self.clay_client.query_table(
            'contacts',
            {'domain': domain}
        )
        
        if not contacts:
            # Trigger enrichment
            self.clay_client.trigger_webhook(
                'https://api.clay.com/v1/enrichment/contacts',
                {'domain': domain}
            )
            # For now, return placeholder
            contacts = [
                {
                    'email': f'security@{domain}',
                    'name': 'Security Team',
                    'title': 'Security',
                    'first_name': 'Security'
                }
            ]
        
        # Prioritize by title
        priority_titles = ['CISO', 'CTO', 'IT Director', 'Security']
        
        def title_score(contact):
            title = contact.get('title', '').upper()
            for i, priority in enumerate(priority_titles):
                if priority.upper() in title:
                    return i
            return 999
        
        contacts.sort(key=title_score)
        
        return contacts
    
    def calculate_send_time(self, score_data: Dict) -> str:
        """Calculate optimal send time based on segment"""
        now = datetime.now()
        
        # High urgency segments get immediate send
        if score_data['segment'] == 'post_breach_survivor':
            send_time = now + timedelta(minutes=15)
        elif score_data['pain_score'] > 85:
            send_time = now + timedelta(hours=1)
        else:
            # Schedule for next business day, 10 AM
            send_time = self.next_business_day_10am()
        
        return send_time.isoformat()
    
    def next_business_day_10am(self) -> datetime:
        """Get next business day at 10 AM"""
        now = datetime.now()
        
        # If it's before 10 AM on a weekday, use today
        if now.weekday() < 5 and now.hour < 10:
            return now.replace(hour=10, minute=0, second=0)
        
        # Otherwise, find next business day
        days_ahead = 1
        while True:
            next_day = now + timedelta(days=days_ahead)
            if next_day.weekday() < 5:  # Monday = 0, Friday = 4
                return next_day.replace(hour=10, minute=0, second=0)
            days_ahead += 1
    
    def get_signature(self) -> str:
        """Get email signature"""
        return """
Best regards,
[Your Name]
Blue Team Alpha
Ex-NSA Cyber Operations
Mobile: [Your Phone]
Schedule a call: [Calendar Link]
"""
```

---

## Phase 4: Clay Integration & Webhook Setup (Days 11-12)

### Step 8: Create Clay Webhook Handler

```python
# src/api/webhook_handler.py
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, List, Optional
import hmac
import hashlib
import json

app = FastAPI()

class CampaignRequest(BaseModel):
    domain: str
    contact_email: str
    contact_name: str
    campaign_type: str
    message: str
    send_time: str

class WebhookResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict]

@app.post("/clay-callback")
async def receive_from_clay(request: Request):
    """Receive scored prospects from Python processing"""
    # Verify webhook signature
    signature = request.headers.get('X-Clay-Signature')
    body = await request.body()
    
    if not verify_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    data = json.loads(body)
    
    # Process the campaign data
    result = process_campaign_data(data)
    
    return WebhookResponse(
        success=True,
        message="Campaign data received",
        data=result
    )

@app.post("/trigger-outreach")
async def trigger_outreach(campaign: CampaignRequest):
    """Send campaign to Clay for delivery"""
    # Prepare data for Clay
    clay_data = {
        'table': 'outreach_queue',
        'data': {
            'domain': campaign.domain,
            'contact_email': campaign.contact_email,
            'contact_name': campaign.contact_name,
            'campaign_type': campaign.campaign_type,
            'message': campaign.message,
            'send_time': campaign.send_time,
            'status': 'ready_to_send'
        }
    }
    
    # Send to Clay webhook
    result = send_to_clay_webhook(clay_data)
    
    return WebhookResponse(
        success=result,
        message="Campaign queued for delivery" if result else "Failed to queue",
        data=clay_data
    )

def verify_signature(body: bytes, signature: str) -> bool:
    """Verify Clay webhook signature"""
    expected_signature = hmac.new(
        config.CLAY_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)

def process_campaign_data(data: Dict) -> Dict:
    """Process campaign data from scoring engine"""
    # Add any additional processing here
    return {
        'campaigns_created': len(data.get('campaigns', [])),
        'total_contacts': len(data.get('contacts', [])),
        'average_pain_score': data.get('average_score', 0)
    }

def send_to_clay_webhook(data: Dict) -> bool:
    """Send data to Clay webhook"""
    try:
        response = requests.post(
            config.CLAY_WEBHOOK_URL,
            json=data,
            headers={
                'X-Signature': generate_signature(data),
                'Content-Type': 'application/json'
            }
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending to Clay: {e}")
        return False

def generate_signature(data: Dict) -> str:
    """Generate signature for Clay webhook"""
    message = json.dumps(data, sort_keys=True)
    signature = hmac.new(
        config.CLAY_WEBHOOK_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Step 9: Create Main Orchestrator

```python
# src/main.py
import schedule
import time
from datetime import datetime
import logging
from typing import List, Dict

# Import our modules
from config.settings import config
from clay_client import ClayClient
from collectors.breach_collector import BreachCollector
from collectors.job_collector import JobPostingCollector
from scoring.edp_scorer import EDPScorer
from campaigns.campaign_generator import CampaignGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BTAOrchestrator:
    def __init__(self):
        # Initialize Clay client
        self.clay_client = ClayClient(
            config.CLAY_API_KEY,
            config.CLAY_WORKSPACE
        )
        
        # Initialize collectors
        self.breach_collector = BreachCollector(self.clay_client)
        self.job_collector = JobPostingCollector(self.clay_client)
        
        # Initialize processors
        self.scorer = EDPScorer(self.clay_client)
        self.campaign_gen = CampaignGenerator(self.clay_client)
        
        self.daily_limit_remaining = config.OUTREACH_DAILY_LIMIT
    
    def run_daily_collection(self):
        """Run all data collectors"""
        logger.info("Starting daily data collection...")
        
        try:
            # Collect breach data
            self.breach_collector.run_collection()
            
            # Collect job postings
            self.job_collector.run_collection()
            
            logger.info("Daily collection complete")
        
        except Exception as e:
            logger.error(f"Collection error: {e}")
    
    def score_new_companies(self):
        """Score all unscored companies"""
        logger.info("Starting scoring process...")
        
        try:
            # Get unscored companies
            unscored = self.clay_client.query_table(
                'company_universe',
                {'scored': False}
            )
            
            logger.info(f"Found {len(unscored)} companies to score")
            
            scored_prospects = []
            
            for company in unscored:
                # Calculate score
                score_data = self.scorer.calculate_company_score(
                    company['domain']
                )
                
                # Only keep if above threshold
                if score_data['pain_score'] >= config.MIN_PAIN_SCORE:
                    scored_prospects.append(score_data)
                
                # Mark as scored
                self.clay_client.add_row('scored_prospects', score_data)
            
            logger.info(f"Scored {len(scored_prospects)} qualified prospects")
            
            return scored_prospects
        
        except Exception as e:
            logger.error(f"Scoring error: {e}")
            return []
    
    def generate_campaigns(self, prospects: List[Dict]):
        """Generate campaigns for qualified prospects"""
        logger.info(f"Generating campaigns for {len(prospects)} prospects...")
        
        campaigns_created = 0
        
        for prospect in prospects:
            if self.daily_limit_remaining <= 0:
                logger.info("Daily limit reached")
                break
            
            try:
                # Get company info
                company = self.clay_client.query_table(
                    'company_universe',
                    {'domain': prospect['domain']}
                )[0]
                
                # Generate campaigns
                campaigns = self.campaign_gen.generate_campaign(
                    company,
                    prospect
                )
                
                # Push to Clay outreach queue
                for campaign in campaigns:
                    self.clay_client.add_row('outreach_queue', campaign)
                    campaigns_created += 1
                    self.daily_limit_remaining -= 1
            
            except Exception as e:
                logger.error(f"Campaign generation error for {prospect['domain']}: {e}")
        
        logger.info(f"Created {campaigns_created} campaigns")
    
    def run_full_cycle(self):
        """Run complete collection -> scoring -> campaign cycle"""
        logger.info("=" * 50)
        logger.info("Starting full outreach cycle")
        logger.info(f"Time: {datetime.now()}")
        
        # Reset daily limit
        self.daily_limit_remaining = config.OUTREACH_DAILY_LIMIT
        
        # Step 1: Collect data
        self.run_daily_collection()
        
        # Step 2: Score companies
        qualified_prospects = self.score_new_companies()
        
        # Step 3: Generate campaigns
        if qualified_prospects:
            self.generate_campaigns(qualified_prospects)
        
        logger.info("Full cycle complete")
        logger.info("=" * 50)
    
    def start_scheduler(self):
        """Start the automated scheduler"""
        # Schedule daily runs
        schedule.every().day.at("06:00").do(self.run_full_cycle)
        
        # Schedule additional scoring runs
        schedule.every().day.at("12:00").do(self.score_new_companies)
        schedule.every().day.at("18:00").do(self.score_new_companies)
        
        logger.info("Scheduler started. Running initial cycle...")
        
        # Run once immediately
        self.run_full_cycle()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

def main():
    """Main entry point"""
    orchestrator = BTAOrchestrator()
    
    # For testing, run once
    # orchestrator.run_full_cycle()
    
    # For production, start scheduler
    orchestrator.start_scheduler()

if __name__ == "__main__":
    main()
```

---

## Phase 5: Testing & Deployment (Days 13-14)

### Step 10: Create Test Suite

```python
# tests/test_integration.py
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
```

### Step 11: Deploy & Monitor

```bash
# deployment/deploy.sh
#!/bin/bash

# 1. Set up environment
echo "Setting up Python environment..."
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Set up database
echo "Setting up database..."
python src/database/setup.py

# 3. Configure environment variables
echo "Configuring environment..."
cp .env.example .env
echo "Please edit .env with your API keys"

# 4. Start Redis for queuing
echo "Starting Redis..."
docker run -d -p 6379:6379 redis

# 5. Start webhook server
echo "Starting webhook server..."
nohup python src/api/webhook_handler.py &

# 6. Start main orchestrator
echo "Starting orchestrator..."
python src/main.py
```

---

## Monitoring & Success Metrics

### Key Metrics Dashboard

```python
# src/monitoring/metrics.py
class MetricsTracker:
    def track_metrics(self):
        return {
            'data_collection': {
                'breaches_found': self.count_breaches_today(),
                'job_postings_found': self.count_jobs_today(),
                'companies_identified': self.count_new_companies()
            },
            'scoring': {
                'companies_scored': self.count_scored_today(),
                'avg_pain_score': self.average_pain_score(),
                'qualified_prospects': self.count_qualified()
            },
            'campaigns': {
                'campaigns_sent': self.count_sent_today(),
                'open_rate': self.calculate_open_rate(),
                'reply_rate': self.calculate_reply_rate(),
                'meeting_rate': self.calculate_meeting_rate()
            },
            'segments': {
                'post_breach': self.count_segment('post_breach_survivor'),
                'skills_gap': self.count_segment('skills_gap_sufferer'),
                'insurance': self.count_segment('insurance_pressured')
            }
        }
```

---

## Success Criteria & Expected Outcomes

### Week 1 Targets
- ✅ 500+ companies identified with pain signals
- ✅ 100+ companies scored above 70
- ✅ 50+ campaigns deployed
- ✅ 15% reply rate achieved

### Week 2 Targets
- ✅ 1,000+ total companies in universe
- ✅ 200+ qualified prospects
- ✅ 10+ meetings booked
- ✅ Automated daily runs stable

### Month 1 Goals
- ✅ 5,000+ companies tracked
- ✅ 500+ high-pain prospects identified
- ✅ 50+ meetings completed
- ✅ 10+ opportunities created
- ✅ $750K+ pipeline generated

---

## Troubleshooting Guide

### Common Issues & Solutions

1. **Clay API Rate Limits**
   - Solution: Implement exponential backoff
   - Use bulk operations instead of individual calls
   - Cache frequently accessed data

2. **n8n Workflow Failures**
   - Solution: Add error handling nodes
   - Implement retry logic with delays
   - Set up email alerts for failures

3. **Low Response Rates**
   - Solution: A/B test subject lines
   - Adjust sending times by segment
   - Refine personalization variables

4. **Data Quality Issues**
   - Solution: Implement validation rules
   - Cross-reference multiple sources
   - Manual review queue for edge cases

---

## Optimization Playbook

### A/B Testing Framework

```python
# src/optimization/ab_testing.py
class ABTester:
    def __init__(self):
        self.tests = {
            'subject_lines': {
                'A': 'Your company found on dark web',
                'B': '[COMPANY] credentials for sale - $4,500',
                'metric': 'open_rate'
            },
            'send_times': {
                'A': '10:00',
                'B': '14:00',
                'metric': 'reply_rate'
            },
            'cta_words': {
                'A': 'Reply REPORT',
                'B': 'Click here for details',
                'metric': 'click_rate'
            }
        }
    
    def assign_variant(self, test_name: str) -> str:
        """Randomly assign variant"""
        import random
        return random.choice(['A', 'B'])
    
    def track_performance(self, test_name: str, variant: str, outcome: bool):
        """Track test results"""
        # Store in database for analysis
        pass
    
    def calculate_winner(self, test_name: str) -> str:
        """Determine winning variant"""
        # Statistical significance calculation
        pass
```

### Performance Optimization

```python
# src/optimization/performance.py
class PerformanceOptimizer:
    def optimize_queries(self):
        """Optimize database queries"""
        # Add indexes
        queries = [
            "CREATE INDEX idx_domain ON company_universe(domain);",
            "CREATE INDEX idx_signal_date ON pain_signals(signal_date);",
            "CREATE INDEX idx_pain_score ON scored_prospects(pain_score);"
        ]
        
    def implement_caching(self):
        """Add Redis caching layer"""
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        
        # Cache company data for 1 hour
        def cache_company(domain: str, data: dict):
            r.setex(f"company:{domain}", 3600, json.dumps(data))
        
        # Cache scores for 24 hours
        def cache_score(domain: str, score: float):
            r.setex(f"score:{domain}", 86400, score)
```

---

## Clay Workflow Configuration

### Setting Up Clay Tables

1. **Navigate to Clay Dashboard**
   - Go to tables.clay.com
   - Click "New Table"

2. **Create Company Universe Table**
   ```
   Columns:
   - company_name (Text)
   - domain (Text, Primary Key)
   - industry (Select from list)
   - employee_count (Number)
   - location (Text)
   - linkedin_url (URL)
   - last_updated (DateTime)
   - data_source (Text)
   - scored (Boolean)
   ```

3. **Create Pain Signals Table**
   ```
   Columns:
   - signal_id (Auto-increment)
   - domain (Text, Foreign Key)
   - signal_type (Select)
   - signal_date (Date)
   - signal_strength (Number 0-1)
   - raw_data (JSON)
   - source (Text)
   ```

4. **Create Outreach Queue Table**
   ```
   Columns:
   - queue_id (Auto-increment)
   - domain (Text)
   - contact_email (Email)
   - contact_name (Text)
   - contact_title (Text)
   - campaign_type (Select)
   - message_personalized (Long Text)
   - scheduled_send (DateTime)
   - status (Select)
   - sent_date (DateTime)
   - opened (Boolean)
   - replied (Boolean)
   ```

### Clay Enrichment Workflows

1. **Contact Finder Workflow**
   - Trigger: New company added
   - Action 1: Find contacts via Clay's People Search
   - Action 2: Enrich with LinkedIn profiles
   - Action 3: Verify email addresses
   - Action 4: Score contact relevance

2. **Technology Stack Enricher**
   - Trigger: Company domain added
   - Action 1: BuiltWith lookup
   - Action 2: Wappalyzer scan
   - Action 3: SSL certificate check
   - Action 4: Update tech_stack column

3. **Company Data Enricher**
   - Trigger: New company added
   - Action 1: Clearbit enrichment
   - Action 2: LinkedIn company lookup
   - Action 3: Industry classification
   - Action 4: Employee count update

### Clay Email Sequencing

1. **Create Email Sequence**
   ```yaml
   Sequence Name: BTA High-Pain Outreach
   
   Email 1:
     Timing: Immediate
     Template: {{campaign_type}} template
     Personalization: Full
     
   Email 2:
     Timing: Day 3 (if no reply)
     Template: Follow-up
     Reference: Previous email
     
   Email 3:
     Timing: Day 7 (if no reply)
     Template: Value add
     Include: Industry report
     
   LinkedIn Touch:
     Timing: Day 10
     Action: Connection request
     Message: Reference email conversation
     
   Email 4:
     Timing: Day 14
     Template: Break-up email
     CTA: Simple yes/no
   ```

2. **Configure Send Settings**
   ```yaml
   Daily Limits:
     - Emails per day: 100
     - Per domain: 5
     - Per contact: 1
   
   Timing:
     - Business hours only: True
     - Timezone: Recipient local
     - Avoid: Mondays, Fridays
   
   Tracking:
     - Open tracking: Enabled
     - Click tracking: Enabled
     - Reply detection: Enabled
   ```

---

## n8n Workflow Templates

### Complete Breach Monitor Workflow

```json
{
  "name": "BTA Complete Breach Monitor",
  "nodes": [
    {
      "name": "Start",
      "type": "n8n-nodes-base.start",
      "position": [250, 300]
    },
    {
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.cron",
      "parameters": {
        "cronExpression": "0 6,12,18 * * *"
      },
      "position": [400, 300]
    },
    {
      "name": "Fetch Multiple Sources",
      "type": "n8n-nodes-base.splitInBatches",
      "parameters": {
        "batchSize": 1
      },
      "position": [550, 300]
    },
    {
      "name": "CA Breach Scraper",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://oag.ca.gov/privacy/databreach/list",
        "responseFormat": "string"
      },
      "position": [700, 200]
    },
    {
      "name": "HHS HIPAA API",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "https://ocrportal.hhs.gov/ocr/breach/breach_report.jsf",
        "jsonParameters": true,
        "options": {
          "bodyContentType": "json"
        },
        "bodyParametersJson": {
          "start": 0,
          "length": 100
        }
      },
      "position": [700, 400]
    },
    {
      "name": "Parse & Transform",
      "type": "n8n-nodes-base.function",
      "parameters": {
        "functionCode": "const items = $input.all();\nconst breaches = [];\n\nitems.forEach(item => {\n  // Parse based on source\n  if (item.json.source === 'ca_ag') {\n    // CA parsing logic\n  } else if (item.json.source === 'hhs') {\n    // HHS parsing logic\n  }\n  \n  // Calculate signal strength\n  const daysSince = calculateDaysSince(item.json.breach_date);\n  const signalStrength = calculateStrength(daysSince);\n  \n  breaches.push({\n    company_name: item.json.company,\n    breach_date: item.json.date,\n    signal_strength: signalStrength,\n    source: item.json.source\n  });\n});\n\nreturn breaches;"
      },
      "position": [850, 300]
    },
    {
      "name": "Send to Clay",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "={{$env.CLAY_WEBHOOK_URL}}",
        "authentication": "headerAuth",
        "headerAuth": {
          "name": "Authorization",
          "value": "Bearer {{$env.CLAY_API_KEY}}"
        },
        "jsonParameters": true,
        "bodyParametersJson": {
          "table": "pain_signals",
          "data": "={{$json}}"
        }
      },
      "position": [1000, 300]
    },
    {
      "name": "Error Handler",
      "type": "n8n-nodes-base.emailSend",
      "parameters": {
        "fromEmail": "alerts@blueteamalpha.com",
        "toEmail": "admin@blueteamalpha.com",
        "subject": "Breach Monitor Error",
        "text": "Error in breach monitoring workflow: {{$json.error}}"
      },
      "position": [850, 500]
    }
  ],
  "connections": {
    "Schedule Trigger": {
      "main": [[{"node": "Fetch Multiple Sources"}]]
    },
    "Fetch Multiple Sources": {
      "main": [
        [{"node": "CA Breach Scraper"}],
        [{"node": "HHS HIPAA API"}]
      ]
    },
    "CA Breach Scraper": {
      "main": [[{"node": "Parse & Transform"}]]
    },
    "HHS HIPAA API": {
      "main": [[{"node": "Parse & Transform"}]]
    },
    "Parse & Transform": {
      "main": [[{"node": "Send to Clay"}]]
    }
  }
}
```

---

## Advanced Features

### Dark Web Monitoring Integration

```python
# src/collectors/darkweb_monitor.py
import requests
from typing import List, Dict

class DarkWebMonitor:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.darkowl.com/v1"
        
    def search_company_mentions(self, company_name: str) -> List[Dict]:
        """Search for company mentions on dark web"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        params = {
            "query": company_name,
            "sources": ["forums", "marketplaces", "chat"],
            "limit": 50
        }
        
        response = requests.get(
            f"{self.base_url}/search",
            headers=headers,
            params=params
        )
        
        mentions = []
        for result in response.json().get('results', []):
            mention = {
                'company': company_name,
                'source': result['source'],
                'date': result['timestamp'],
                'context': result['snippet'],
                'threat_level': self.assess_threat_level(result),
                'url': result.get('url', ''),
                'signal_type': 'dark_web_mention',
                'signal_strength': self.calculate_urgency(result)
            }
            mentions.append(mention)
        
        return mentions
    
    def assess_threat_level(self, result: Dict) -> str:
        """Assess threat level from dark web mention"""
        keywords = result.get('snippet', '').lower()
        
        if any(word in keywords for word in ['ransomware', 'encrypted', 'locked']):
            return 'critical'
        elif any(word in keywords for word in ['credentials', 'passwords', 'access']):
            return 'high'
        elif any(word in keywords for word in ['vulnerability', 'exploit', 'bug']):
            return 'medium'
        else:
            return 'low'
    
    def calculate_urgency(self, result: Dict) -> float:
        """Calculate urgency score for dark web mention"""
        threat_scores = {
            'critical': 1.0,
            'high': 0.8,
            'medium': 0.5,
            'low': 0.3
        }
        
        threat_level = self.assess_threat_level(result)
        base_score = threat_scores[threat_level]
        
        # Increase score for recent mentions
        days_old = self.calculate_age(result['timestamp'])
        if days_old < 1:
            base_score = min(base_score + 0.3, 1.0)
        elif days_old < 7:
            base_score = min(base_score + 0.2, 1.0)
        elif days_old < 30:
            base_score = min(base_score + 0.1, 1.0)
        
        return base_score
```

### Insurance Intelligence Collector

```python
# src/collectors/insurance_intel.py
class InsuranceIntelCollector:
    def __init__(self, clay_client):
        self.clay_client = clay_client
        self.insurers = [
            'Chubb', 'AIG', 'Travelers', 'Hartford',
            'Zurich', 'Liberty Mutual', 'CNA'
        ]
        
    def collect_insurance_signals(self) -> List[Dict]:
        """Collect cyber insurance market signals"""
        signals = []
        
        # Check insurance news
        signals.extend(self.scan_insurance_news())
        
        # Check rate filing databases
        signals.extend(self.check_rate_filings())
        
        # Check claim databases
        signals.extend(self.check_claims_data())
        
        return signals
    
    def scan_insurance_news(self) -> List[Dict]:
        """Scan for insurance requirement changes"""
        # Implementation would scan insurance industry news
        # for mentions of new requirements, denials, etc.
        pass
    
    def estimate_renewal_dates(self, company_domain: str) -> Dict:
        """Estimate insurance renewal date"""
        # Most policies renew annually
        # Can estimate based on fiscal year or incorporation date
        company = self.clay_client.query_table(
            'company_universe',
            {'domain': company_domain}
        )[0]
        
        # Placeholder logic
        import random
        months_until_renewal = random.randint(1, 12)
        
        return {
            'domain': company_domain,
            'estimated_renewal_months': months_until_renewal,
            'confidence': 0.6
        }
```

---

## ROI Calculator

### Calculate Expected Returns

```python
# src/analytics/roi_calculator.py
class ROICalculator:
    def __init__(self):
        self.metrics = {
            'avg_deal_size': 75000,
            'close_rate': 0.15,
            'sales_cycle_days': 45,
            'cost_per_lead': 50,
            'monthly_costs': 5000  # Tools + infrastructure
        }
    
    def calculate_monthly_roi(self, month: int = 1) -> Dict:
        """Calculate expected ROI by month"""
        # Ramp-up curve
        ramp_multipliers = {
            1: 0.3, 2: 0.5, 3: 0.7,
            4: 0.85, 5: 0.95, 6: 1.0
        }
        
        multiplier = ramp_multipliers.get(month, 1.0)
        
        # Expected outcomes
        leads_generated = 500 * multiplier
        qualified_leads = leads_generated * 0.3
        opportunities = qualified_leads * 0.4
        closed_deals = opportunities * self.metrics['close_rate']
        
        # Revenue
        revenue = closed_deals * self.metrics['avg_deal_size']
        
        # Costs
        lead_costs = leads_generated * self.metrics['cost_per_lead']
        total_costs = lead_costs + self.metrics['monthly_costs']
        
        # ROI
        roi = (revenue - total_costs) / total_costs * 100
        
        return {
            'month': month,
            'leads': int(leads_generated),
            'qualified': int(qualified_leads),
            'opportunities': int(opportunities),
            'closed_deals': closed_deals,
            'revenue': revenue,
            'costs': total_costs,
            'roi_percent': roi,
            'payback_months': total_costs / (revenue / month) if revenue > 0 else None
        }
    
    def project_annual(self) -> Dict:
        """Project annual performance"""
        annual = {
            'total_revenue': 0,
            'total_costs': 0,
            'total_deals': 0,
            'months': []
        }
        
        for month in range(1, 13):
            month_data = self.calculate_monthly_roi(month)
            annual['months'].append(month_data)
            annual['total_revenue'] += month_data['revenue']
            annual['total_costs'] += month_data['costs']
            annual['total_deals'] += month_data['closed_deals']
        
        annual['annual_roi'] = (
            (annual['total_revenue'] - annual['total_costs']) / 
            annual['total_costs'] * 100
        )
        
        return annual
```

---

## Final Checklist

### Pre-Launch Checklist

- [ ] **API Keys Configured**
  - [ ] Clay API key set
  - [ ] n8n webhooks configured
  - [ ] Dark web monitoring API (optional)
  - [ ] Wappalyzer API key set

- [ ] **Clay Setup Complete**
  - [ ] All tables created
  - [ ] Webhooks configured
  - [ ] Enrichment workflows active
  - [ ] Email sequences built

- [ ] **n8n Workflows Running**
  - [ ] Breach monitor active
  - [ ] Job posting collector active
  - [ ] Error handling configured
  - [ ] Scheduling verified

- [ ] **Python Environment Ready**
  - [ ] Dependencies installed
  - [ ] Environment variables set
  - [ ] Database initialized
  - [ ] Tests passing

- [ ] **Monitoring Active**
  - [ ] Metrics dashboard live
  - [ ] Error alerts configured
  - [ ] Performance tracking enabled
  - [ ] A/B tests configured

### Week 1 Operations

**Day 1:**
- Launch breach monitoring
- Verify Clay data flow
- Send first 10 test campaigns

**Day 2:**
- Enable job posting collection
- Score first batch of companies
- Deploy 50 campaigns

**Day 3:**
- Add dark web monitoring
- Implement insurance signals
- Scale to 100 campaigns

**Day 4:**
- Analyze initial responses
- Optimize message templates
- Scale to 200 campaigns

**Day 5:**
- Review metrics
- Adjust scoring thresholds
- Full automation active

---

## Support & Troubleshooting Contacts

### Technical Support
- Clay Support: support@clay.com
- n8n Community: community.n8n.io
- Python Issues: Stack Overflow with tags [python, clay-api]

### Data Sources
- Breach Databases: Check state AG sites
- Job Boards: Indeed, LinkedIn APIs
- Dark Web: DarkOwl, Recorded Future

### Emergency Procedures
1. Campaign Pause: `python src/scripts/pause_all.py`
2. Data Backup: `python src/scripts/backup_data.py`
3. Roll Back: `git checkout stable-version`

---

This completes your comprehensive Blue Team Alpha implementation guide. The system is designed to scale from manual testing to full automation, with clear metrics for success at each stage.