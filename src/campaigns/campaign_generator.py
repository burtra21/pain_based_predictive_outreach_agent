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