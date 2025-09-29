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
        """Collect from LinkedIn using Clay's LinkedIn Jobs integration"""
        jobs = []
        
        try:
            print("Collecting LinkedIn job postings via Clay...")
            
            # Use Clay's LinkedIn Jobs enrichment
            linkedin_jobs_data = self.collect_via_clay_linkedin_jobs()
            jobs.extend(linkedin_jobs_data)
            
            # Also try direct LinkedIn search if Clay doesn't have enough data
            if len(jobs) < 10:
                direct_jobs = self.collect_direct_linkedin_jobs()
                jobs.extend(direct_jobs)
            
        except Exception as e:
            print(f"LinkedIn collection error: {e}")
        
        return jobs
    
    def collect_via_clay_linkedin_jobs(self) -> List[Dict]:
        """Use Clay's LinkedIn Jobs enrichment to find security job postings"""
        jobs = []
        
        try:
            # Define security job search terms
            security_roles = [
                "Chief Information Security Officer",
                "CISO",
                "Security Director", 
                "Director of Security",
                "Security Manager",
                "SOC Manager",
                "Security Analyst",
                "Security Engineer",
                "Threat Hunter",
                "Incident Response Manager",
                "Cybersecurity Manager",
                "Information Security Manager"
            ]
            
            for role in security_roles:
                try:
                    # Use Clay's LinkedIn Jobs enrichment
                    # This triggers Clay to search LinkedIn Jobs for the role
                    enrichment_data = {
                        'job_title': role,
                        'location': 'United States',
                        'posted_within': '30',  # Last 30 days
                        'job_type': 'full-time'
                    }
                    
                    # Trigger Clay enrichment for LinkedIn Jobs
                    clay_response = self.clay_client.trigger_webhook(
                        'https://api.clay.com/v1/enrichment/linkedin-jobs',
                        enrichment_data
                    )
                    
                    if clay_response:
                        # Process the Clay response
                        processed_jobs = self.process_clay_linkedin_jobs(clay_response, role)
                        jobs.extend(processed_jobs)
                    
                    time.sleep(2)  # Rate limiting
                    
                except Exception as e:
                    print(f"Error collecting LinkedIn jobs for {role}: {e}")
                    continue
            
        except Exception as e:
            print(f"Error in Clay LinkedIn Jobs collection: {e}")
        
        return jobs
    
    def process_clay_linkedin_jobs(self, clay_data: Dict, role: str) -> List[Dict]:
        """Process LinkedIn Jobs data from Clay"""
        jobs = []
        
        try:
            # Extract job postings from Clay response
            job_postings = clay_data.get('jobs', [])
            
            for job in job_postings:
                if not isinstance(job, dict):
                    continue
                
                # Calculate days open
                posted_date = job.get('posted_date', '')
                days_open = self.calculate_days_open(posted_date)
                
                # Only include jobs open for more than 30 days (indicating difficulty filling)
                if days_open > 30:
                    job_data = {
                        'company_name': job.get('company_name', ''),
                        'job_title': job.get('job_title', role),
                        'location': job.get('location', ''),
                        'posted_date': posted_date,
                        'days_open': days_open,
                        'signal_type': self.categorize_vacancy_signal(days_open, role),
                        'signal_strength': self.calculate_vacancy_score(days_open, role),
                        'source': 'linkedin_via_clay',
                        'url': job.get('job_url', ''),
                        'linkedin_job_id': job.get('job_id', ''),
                        'company_linkedin_url': job.get('company_linkedin_url', '')
                    }
                    
                    # Validate job data
                    if job_data['company_name'] and job_data['days_open'] > 0:
                        jobs.append(job_data)
                        print(f"Found LinkedIn job: {job_data['company_name']} - {role} ({days_open} days)")
            
        except Exception as e:
            print(f"Error processing Clay LinkedIn Jobs data: {e}")
        
        return jobs
    
    def collect_direct_linkedin_jobs(self) -> List[Dict]:
        """Fallback: Direct LinkedIn job search (if Clay doesn't have enough data)"""
        jobs = []
        
        try:
            # This would be a fallback method if Clay doesn't return enough data
            # For now, we'll use a simplified approach
            
            # Search for security jobs on LinkedIn (public search)
            security_search_terms = [
                "CISO",
                "Chief Information Security Officer", 
                "Security Director",
                "Cybersecurity Manager"
            ]
            
            for term in security_search_terms:
                try:
                    # Use LinkedIn's public job search
                    response = self.session.get(
                        'https://www.linkedin.com/jobs/search',
                        params={
                            'keywords': term,
                            'location': 'United States',
                            'f_TPR': 'r2592000',  # Last 30 days
                            'f_JT': 'F',  # Full-time
                            'start': 0,
                            'count': 25
                        },
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        # Parse LinkedIn job search results
                        linkedin_jobs = self.parse_linkedin_job_search(response.text, term)
                        jobs.extend(linkedin_jobs)
                    
                    time.sleep(3)  # Respectful delay
                    
                except Exception as e:
                    print(f"Error in direct LinkedIn search for {term}: {e}")
                    continue
            
        except Exception as e:
            print(f"Error in direct LinkedIn job collection: {e}")
        
        return jobs
    
    def parse_linkedin_job_search(self, html_content: str, search_term: str) -> List[Dict]:
        """Parse LinkedIn job search results"""
        jobs = []
        
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find job listings in LinkedIn's HTML structure
            job_cards = soup.find_all('div', {'class': 'job-search-card'})
            
            for card in job_cards[:10]:  # Limit to first 10
                try:
                    # Extract job information
                    company_elem = card.find('h4', {'class': 'job-search-card__subtitle'})
                    title_elem = card.find('h3', {'class': 'job-search-card__title'})
                    location_elem = card.find('span', {'class': 'job-search-card__location'})
                    date_elem = card.find('time')
                    
                    if company_elem and title_elem:
                        company_name = company_elem.get_text().strip()
                        job_title = title_elem.get_text().strip()
                        location = location_elem.get_text().strip() if location_elem else ''
                        posted_date = date_elem.get('datetime', '') if date_elem else ''
                        
                        # Calculate days open
                        days_open = self.calculate_days_open(posted_date)
                        
                        # Only include jobs open for more than 30 days
                        if days_open > 30:
                            job_data = {
                                'company_name': company_name,
                                'job_title': job_title,
                                'location': location,
                                'posted_date': posted_date,
                                'days_open': days_open,
                                'signal_type': self.categorize_vacancy_signal(days_open, job_title),
                                'signal_strength': self.calculate_vacancy_score(days_open, job_title),
                                'source': 'linkedin_direct',
                                'url': '',  # LinkedIn URLs are complex to extract
                                'search_term': search_term
                            }
                            
                            jobs.append(job_data)
                            print(f"Found LinkedIn job: {company_name} - {job_title} ({days_open} days)")
                
                except Exception as e:
                    print(f"Error parsing LinkedIn job card: {e}")
                    continue
            
        except Exception as e:
            print(f"Error parsing LinkedIn job search: {e}")
        
        return jobs
    
    def run_collection(self):
        """Main collection orchestration"""
        print("Starting job posting collection...")
        
        # Collect from LinkedIn (primary method)
        linkedin_jobs = self.collect_linkedin_jobs()
        
        # Collect from Indeed (fallback)
        indeed_jobs = self.collect_indeed_jobs()
        
        # Combine all jobs
        all_jobs = linkedin_jobs + indeed_jobs
        
        print(f"Collected {len(all_jobs)} total job postings")
        print(f"LinkedIn jobs: {len(linkedin_jobs)}")
        print(f"Indeed jobs: {len(indeed_jobs)}")
        
        # Push to Clay
        if all_jobs:
            self.push_to_clay(all_jobs)
        
        print("Job posting collection complete")
    
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