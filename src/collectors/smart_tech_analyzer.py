"""
Smart Tech Stack Analyzer
Intelligently uses BuiltWith API or Clay data based on what's available
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime
import json

class SmartTechStackAnalyzer:
    """Intelligently analyzes tech stack using optimal data source"""
    
    def __init__(self, clay_client, builtwith_api_key: Optional[str] = None):
        self.clay_client = clay_client
        self.builtwith_api_key = builtwith_api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BTA-TechAnalyzer/1.0'
        })
        
        # Security tool indicators
        self.security_tools = {
            'mdr': ['crowdstrike', 'sentinelone', 'carbon_black', 'cylance'],
            'siem': ['splunk', 'qradar', 'arcsight', 'logrhythm', 'elastic'],
            'edr': ['crowdstrike', 'sentinelone', 'carbon_black', 'cylance', 'microsoft_defender'],
            'firewall': ['palo_alto', 'fortinet', 'cisco_asa', 'checkpoint', 'sonicwall'],
            'email_security': ['proofpoint', 'mimecast', 'barracuda', 'cisco_email'],
            'web_security': ['zscaler', 'cloudflare', 'imperva', 'f5'],
            'backup': ['veeam', 'commvault', 'rubrik', 'cohesity'],
            'monitoring': ['datadog', 'new_relic', 'solarwinds', 'prtg']
        }
        
        # Compliance tools
        self.compliance_tools = {
            'hipaa': ['hipaa_compliance', 'healthcare_security'],
            'sox': ['sox_compliance', 'financial_controls'],
            'pci': ['pci_compliance', 'payment_security'],
            'gdpr': ['gdpr_compliance', 'data_privacy']
        }
    
    def analyze_tech_stack(self, company: Dict) -> Dict:
        """Analyze tech stack using optimal data source"""
        
        domain = company.get('domain', '')
        company_name = company.get('company_name', '')
        
        if not domain:
            return {'error': 'No domain provided'}
        
        # Check if we have BuiltWith data in Clay first
        clay_tech_data = self.get_tech_data_from_clay(domain)
        
        if clay_tech_data and self.is_comprehensive_tech_data(clay_tech_data):
            # Use Clay data - it's already enriched
            print(f"Using Clay BuiltWith data for {domain}")
            return self.analyze_clay_tech_data(clay_tech_data, company)
        
        elif self.builtwith_api_key:
            # Use BuiltWith API for fresh data
            print(f"Using BuiltWith API for {domain}")
            return self.analyze_with_builtwith_api(domain, company)
        
        else:
            # Fallback to basic analysis
            print(f"Using basic analysis for {domain}")
            return self.analyze_basic_tech_stack(domain, company)
    
    def get_tech_data_from_clay(self, domain: str) -> Optional[Dict]:
        """Get tech stack data from Clay if it exists"""
        try:
            # Query Clay for tech stack data
            tech_data = self.clay_client.query_table(
                'company_universe',
                {'domain': domain}
            )
            
            if tech_data and len(tech_data) > 0:
                return tech_data[0]
            
        except Exception as e:
            print(f"Error getting tech data from Clay: {e}")
        
        return None
    
    def is_comprehensive_tech_data(self, tech_data: Dict) -> bool:
        """Check if Clay tech data is comprehensive enough"""
        
        # Check for key tech stack fields
        tech_fields = [
            'technologies', 'security_tools', 'compliance_tools',
            'web_technologies', 'server_technologies', 'analytics_tools'
        ]
        
        has_tech_data = any(
            tech_data.get(field) and len(str(tech_data.get(field))) > 10 
            for field in tech_fields
        )
        
        return has_tech_data
    
    def analyze_clay_tech_data(self, tech_data: Dict, company: Dict) -> Dict:
        """Analyze tech stack data from Clay"""
        
        domain = company.get('domain', '')
        company_name = company.get('company_name', '')
        
        # Extract technologies from Clay data
        technologies = []
        
        # Parse different tech data formats from Clay
        tech_fields = ['technologies', 'security_tools', 'compliance_tools', 'web_technologies']
        
        for field in tech_fields:
            field_data = tech_data.get(field, '')
            if field_data:
                if isinstance(field_data, str):
                    # Parse comma-separated or JSON string
                    try:
                        if field_data.startswith('['):
                            techs = json.loads(field_data)
                        else:
                            techs = [t.strip() for t in field_data.split(',')]
                        technologies.extend(techs)
                    except:
                        technologies.append(field_data)
                elif isinstance(field_data, list):
                    technologies.extend(field_data)
        
        # Analyze for security gaps
        security_analysis = self.analyze_security_gaps(technologies)
        
        # Generate signals if gaps found
        signals = []
        if security_analysis['gaps']:
            signal = {
                'company_name': company_name,
                'domain': domain,
                'signal_type': 'security_tech_gaps',
                'signal_date': datetime.utcnow().isoformat(),
                'signal_strength': security_analysis['gap_score'],
                'raw_data': {
                    'technologies_found': technologies[:20],  # Limit for storage
                    'security_gaps': security_analysis['gaps'],
                    'gap_score': security_analysis['gap_score'],
                    'data_source': 'clay_builtwith',
                    'confidence': 'high'
                },
                'source': 'tech_stack_analysis'
            }
            signals.append(signal)
        
        return {
            'technologies': technologies,
            'security_analysis': security_analysis,
            'signals': signals,
            'data_source': 'clay'
        }
    
    def analyze_with_builtwith_api(self, domain: str, company: Dict) -> Dict:
        """Analyze tech stack using BuiltWith API"""
        
        try:
            # BuiltWith API call
            response = self.session.get(
                'https://api.builtwith.com/v20/api.json',
                params={
                    'KEY': self.builtwith_api_key,
                    'LOOKUP': domain,
                    'HIDETEXT': 'yes',
                    'HIDEDL': 'yes'
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                technologies = self.extract_technologies_from_builtwith(data)
                
                # Analyze for security gaps
                security_analysis = self.analyze_security_gaps(technologies)
                
                # Generate signals if gaps found
                signals = []
                if security_analysis['gaps']:
                    signal = {
                        'company_name': company.get('company_name', ''),
                        'domain': domain,
                        'signal_type': 'security_tech_gaps',
                        'signal_date': datetime.utcnow().isoformat(),
                        'signal_strength': security_analysis['gap_score'],
                        'raw_data': {
                            'technologies_found': technologies[:20],
                            'security_gaps': security_analysis['gaps'],
                            'gap_score': security_analysis['gap_score'],
                            'data_source': 'builtwith_api',
                            'confidence': 'high'
                        },
                        'source': 'tech_stack_analysis'
                    }
                    signals.append(signal)
                
                return {
                    'technologies': technologies,
                    'security_analysis': security_analysis,
                    'signals': signals,
                    'data_source': 'builtwith_api'
                }
            
            else:
                print(f"BuiltWith API error: {response.status_code}")
                return self.analyze_basic_tech_stack(domain, company)
                
        except Exception as e:
            print(f"BuiltWith API error: {e}")
            return self.analyze_basic_tech_stack(domain, company)
    
    def extract_technologies_from_builtwith(self, data: Dict) -> List[str]:
        """Extract technologies from BuiltWith API response"""
        
        technologies = []
        
        try:
            # Parse BuiltWith response structure
            results = data.get('Results', [])
            
            for result in results:
                paths = result.get('Result', {}).get('Paths', [])
                
                for path in paths:
                    technologies_list = path.get('Technologies', [])
                    
                    for tech in technologies_list:
                        tech_name = tech.get('Name', '')
                        if tech_name:
                            technologies.append(tech_name.lower())
            
            # Remove duplicates and return
            return list(set(technologies))
            
        except Exception as e:
            print(f"Error extracting technologies from BuiltWith: {e}")
            return []
    
    def analyze_basic_tech_stack(self, domain: str, company: Dict) -> Dict:
        """Basic tech stack analysis without external APIs"""
        
        try:
            # Basic HTTP analysis
            response = self.session.get(f'https://{domain}', timeout=10)
            
            technologies = []
            
            # Check headers for technology indicators
            headers = response.headers
            
            # Server technology
            server = headers.get('Server', '').lower()
            if server:
                technologies.append(f'server:{server}')
            
            # Security headers
            security_headers = [
                'Strict-Transport-Security',
                'X-Content-Type-Options',
                'X-Frame-Options',
                'X-XSS-Protection',
                'Content-Security-Policy'
            ]
            
            for header in security_headers:
                if header in headers:
                    technologies.append(f'security_header:{header.lower()}')
            
            # Basic security analysis
            security_analysis = self.analyze_security_gaps(technologies)
            
            return {
                'technologies': technologies,
                'security_analysis': security_analysis,
                'signals': [],  # Basic analysis rarely generates signals
                'data_source': 'basic_http'
            }
            
        except Exception as e:
            print(f"Basic tech analysis error: {e}")
            return {
                'technologies': [],
                'security_analysis': {'gaps': [], 'gap_score': 0},
                'signals': [],
                'data_source': 'error'
            }
    
    def analyze_security_gaps(self, technologies: List[str]) -> Dict:
        """Analyze technologies for security gaps"""
        
        gaps = []
        gap_score = 0.0
        
        # Check for missing security tools
        for category, tools in self.security_tools.items():
            has_tool = any(tool in ' '.join(technologies) for tool in tools)
            
            if not has_tool:
                gaps.append(f'missing_{category}')
                gap_score += 0.15  # Each missing category adds 0.15
        
        # Check for missing compliance tools
        for compliance_type, tools in self.compliance_tools.items():
            has_compliance = any(tool in ' '.join(technologies) for tool in tools)
            
            if not has_compliance:
                gaps.append(f'missing_{compliance_type}_compliance')
                gap_score += 0.1  # Each missing compliance adds 0.1
        
        # Check for outdated technologies
        outdated_techs = ['php', 'apache', 'mysql', 'jquery']
        for tech in outdated_techs:
            if tech in ' '.join(technologies):
                gaps.append(f'outdated_technology:{tech}')
                gap_score += 0.05
        
        # Cap gap score at 1.0
        gap_score = min(gap_score, 1.0)
        
        return {
            'gaps': gaps,
            'gap_score': gap_score,
            'technologies_analyzed': len(technologies)
        }
    
    def get_tech_stack_recommendations(self, security_analysis: Dict) -> List[str]:
        """Get recommendations based on tech stack analysis"""
        
        recommendations = []
        gaps = security_analysis.get('gaps', [])
        
        gap_recommendations = {
            'missing_mdr': 'Implement Managed Detection and Response (MDR) solution',
            'missing_siem': 'Deploy Security Information and Event Management (SIEM)',
            'missing_edr': 'Implement Endpoint Detection and Response (EDR)',
            'missing_firewall': 'Deploy next-generation firewall',
            'missing_email_security': 'Implement email security solution',
            'missing_web_security': 'Deploy web application firewall',
            'missing_backup': 'Implement enterprise backup solution',
            'missing_monitoring': 'Deploy infrastructure monitoring',
            'missing_hipaa_compliance': 'Implement HIPAA compliance tools',
            'missing_sox_compliance': 'Deploy SOX compliance monitoring',
            'missing_pci_compliance': 'Implement PCI DSS compliance tools',
            'missing_gdpr_compliance': 'Deploy GDPR compliance solution'
        }
        
        for gap in gaps:
            if gap in gap_recommendations:
                recommendations.append(gap_recommendations[gap])
        
        return recommendations
