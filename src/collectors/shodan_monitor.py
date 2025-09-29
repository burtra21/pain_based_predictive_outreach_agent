"""
Shodan Network Vulnerability Monitor for Pain-Based Predictive Outreach

High-value pain signals from network exposure analysis:
- Exposed databases (MySQL, PostgreSQL, MongoDB)
- Unsecured IoT devices 
- Vulnerable web services (OpenSSL, outdated servers)
- RDP/VNC exposures
- Critical port exposures (SSH, Telnet, FTP)
- Industrial control systems (ICS/SCADA)
- Docker/Kubernetes exposures
- Shadowy Brokers (malware, command & control)
"""

import shodan
import socket
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import re
from urllib.parse import urlparse
import time

logger = logging.getLogger(__name__)

class ShodanMonitor:
    def __init__(self, api_key: str):
        """Initialize Shodan monitor with API key"""
        self.api = shodan.Shodan(api_key)
        self.rate_limit_count = 0
        self.rate_limit_window_start = datetime.now()
        
        # Pain signal priorities for outreach timing
        self.CRITICAL_EXPOSURES = {
            'database': ['mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch'],
            'remote_access': ['rdp', 'vnc', 'teamviewer', 'ssh', 'telnet'],
            'iot_vulnerable': ['default_password', 'backdoor', 'vulnerable_firmware'],
            'web_exposed': ['exposed_config', 'debug_mode', 'development_server'],
            'industrial': ['scada', 'modbus', 'profibus', 's7'],
            'container': ['docker', 'kubernetes', 'swarm'],
        }
        
        # Security gaps detected by Shodan
        self.SECURITY_GAPS = {
            'misconfigured': ['default_login', 'anonymous_access', 'weak_crypto'],
            'outdated': ['old_version', 'vulnerable_version', 'deprecated_protocol'],
            'exposed_sensitive': ['password_file', 'config_file', 'backup_file'],
            'malicious': ['malware', 'botnet', 'cnc', 'c2']
        }

    def check_rate_limit(self) -> None:
        """Respect Shodan API rate limits"""
        now = datetime.now()
        if now - self.rate_limit_window_start > timedelta(minutes=1):
            self.rate_limit_count = 0
            self.rate_limit_window_start = now
            
        if self.rate_limit_count >= 45:  # Conservative limit
            sleep_time = 60 - (now - self.rate_limit_window_start).seconds
            if sleep_time > 0:
                time.sleep(sleep_time)
                self.rate_limit_count = 0
                self.rate_limit_window_start = datetime.now()

    def extract_domain_ips(self, domain: str) -> List[str]:
        """Extract IP addresses for a domain"""
        try:
            # Try to resolve domain
            ips = []
            result = socket.getaddrinfo(domain, None)
            for item in result:
                ip = item[4][0]
                if ip not in ips:
                    ips.append(ip)
            return ips
        except Exception as e:
            logger.warning(f"Failed to resolve domain {domain}: {e}")
            return []

    def analyze_domain_exposure(self, company_data: Dict) -> List[Dict]:
        """Analyze domain for network exposures and vulnerabilities"""
        domain = company_data.get('domain')
        company_name = company_data.get('company_name', 'Unknown')
        
        if not domain:
            logger.warning(f"No domain provided for {company_name}")
            return []

        self.check_rate_limit()
        signals = []
        
        try:
            # Search Shodan for host information
            logger.info(f"Scanning Shodan for {domain} exposures")
            
            # Get IPs for domain
            ips = self.extract_domain_ips(domain)
            
            all_results = []
            
            # Search by domain
            if domain:
                try:
                    results = self.api.search(f"hostname:{domain}")
                    all_results.extend(results['matches'])
                    self.rate_limit_count += 1
                except shodan.exception.APIError as e:
                    logger.error(f"Shodan API error searching by hostname: {e}")
            
            # Search by IPs
            for ip in ips[:3]:  # Limit to top 3 IPs
                try:
                    self.check_rate_limit()
                    results = self.api.search(f"ip:{ip}")
                    all_results.extend(results['matches'])
                    self.rate_limit_count += 1
                except shodan.exception.APIError as e:
                    logger.error(f"Shodan API error searching by IP {ip}: {e}")
            
            # Analyze results for pain signals
            signals = self._analyze_shodan_results(all_results, company_data)
            
            logger.info(f"Found {len(signals)} pain signals for {domain}")
            
        except Exception as e:
            logger.error(f"Error analyzing domain {domain} with Shodan: {e}", exc_info=True)
            
        return signals

    def _analyze_shodan_results(self, results: List[Dict], company_data: Dict) -> List[Dict]:
        """Analyze Shodan search results for pain signals"""
        signals = []
        domain = company_data.get('domain', '')
        company_name = company_data.get('company_name', 'Unknown')
        
        # Track exposures by category
        exposures = {}
        critical_findings = []
        
        for result in results:
            try:
                # Extract key data
                ip = result.get('ip_str', '')
                port = result.get('port', 0)
                product = result.get('product', '')
                version = result.get('version', '')
                banner = result.get('data', '')
                
                # Analyze for critical exposures
                self._categorize_exposures(exposures, critical_findings, result)
                
            except Exception as e:
                logger.warning(f"Error processing Shodan result: {e}")
                continue
        
        # Generate pain signals based on findings
        signals.extend(self._generate_exposure_signals(exposures, company_data))
        signals.extend(self._give_critical_signals(critical_findings, company_data))
        
        return signals

    def _categorize_exposures(self, exposures: Dict, critical_findings: List[Dict], result: Dict):
        """Categorize exposures by type and severity"""
        ip = result.get('ip_str', '')
        port = result.get('port', 0)
        product = result.get('product', '').lower()
        banner = result.get('data', '').lower()
        
        # Database exposures
        for db in self.CRITICAL_EXPOSURES['database']:
            if db in product or db in banner:
                exposures.setdefault('databases', []).append({
                    'ip': ip,
                    'port': port,
                    'type': db,
                    'product': product,
                    'risk': 'HIGH'
                })
                if 'anonymous' in banner or 'default_password' in banner:
                    critical_findings.append({
                        'type': 'exposed_database',
                        'severity': 'CRITICAL',
                        'description': f'Exposed {db} database with anonymous/default access',
                        'ip': ip,
                        'port': port
                    })
        
        # Remote access exposures
        for access in self.CRITICAL_EXPOSURES['remote_access']:
            if access in banner:
                exposures.setdefault('remote_access', []).append({
                    'ip': ip,
                    'port': port,
                    'type': access,
                    'risk': 'HIGH'
                })
        
        # Industrial control systems
        for ics in self.CRITICAL_EXPOSURES['industrial']:
            if ics in banner or ics in product:
                exposures.setdefault('industrial_systems', []).append({
                    'ip': ip,
                    'port': port,
                    'type': ics,
                    'risk': 'CRITICAL'
                })
                
        # IoT vulnerabilities
        for iot_vuln in self.CRITICAL_EXPOSURES['iot_vulnerable']:
            if iot_vuln.replace('_', ' ') in banner:
                critical_findings.append({
                    'type': 'iot_vulnerability',
                    'severity': 'HIGH',
                    'description': f'IoT device with {iot_vuln}',
                    'ip': ip,
                    'port': port
                })

    def _generate_exposure_signals(self, exposures: Dict, company_data: Dict) -> List[Dict]:
        """Generate pain signals from categorized exposures"""
        signals = []
        company_name = company_data.get('company_name', 'Unknown')
        domain = company_data.get('domain', '')
        
        for category, items in exposures.items():
            if not items:
                continue
                
            signal_type = f'exposed_{category}'
            risk_level = 'HIGH' if category in ['databases', 'industrial_systems'] else 'MEDIUM'
            
            # Create aggregated signal
            signal = {
                'signal_type': signal_type,
                'signal_date': datetime.utcnow().isoformat(),
                'signal_strength': 0.9 if risk_level == 'HIGH' else 0.7,
                'source': 'shodan_monitor',
                'company_name': company_name,
                'domain': domain,
                'raw_data': {
                    'category': category,
                    'exposure_count': len(items),
                    'exposures': items[:5],  # Limit to top 5
                    'risk_level': risk_level
                },
                'priority_score': 0.9 if risk_level == 'HIGH' else 0.7
            }
            
            signals.append(signal)
            
            # Create campaign suggestion
            signal['campaign_type'] = self._suggest_campaign_for_exposure(category)
            
        return signals

    def _give_critical_signals(self, critical_findings: List[Dict], company_data: Dict) -> List[Dict]:
        """Generate urgent pain signals from critical findings"""
        signals = []
        company_name = company_data.get('company_name', 'Unknown')
        domain = company_data.get('domain', '')
        
        for finding in critical_findings:
            signal = {
                'signal_type': finding['type'],
                'signal_date': datetime.utcnow().isoformat(),
                'signal_strength': 1.0 if finding['severity'] == 'CRITICAL' else 0.9,
                'source': 'shodan_critical',
                'company_name': company_name,
                'domain': domain,
                'raw_data': {
                    'description': finding['description'],
                    'ip': finding.get('ip'),
                    'port': finding.get('port'),
                    'severity': finding['severity']
                },
                'priority_score': 1.0,
                'campaign_type': 'emergency_response'
            }
            
            signals.append(signal)
            
        return signals

    def _suggest_campaign_for_exposure(self, category: str) -> str:
        """Suggest campaign type based on exposure category"""
        campaigns = {
            'databases': 'database_security_alert',
            'remote_access': 'exposed_access_points', 
            'industrial_systems': 'ics_security_critical',
            'containers': 'container_security_breach'
        }
        return campaigns.get(category, 'network_security_assessment')

    def scan_critical_ports(self, domain: str) -> List[Dict]:
        """Scan for critical port exposures on a domain"""
        signals = []
        
        if not domain:
            return signals
            
        try:
            self.check_rate_limit()
            
            # Search for common vulnerable ports
            critical_ports = ['21', '22', '23', '80', '443', '3389', '5900', '6379', '5432', '3306']
            
            for port in critical_ports:
                try:
                    self.check_rate_limit()
                    results = self.api.search(f"hostname:{domain} port:{port}")
                    
                    if results['total'] > 0:
                        signal = {
                            'signal_type': f'port_{port}_exposed',
                            'signal_date': datetime.utcnow().isoformat(),
                            'signal_strength': 0.8,
                            'source': 'shodan_port_scan',
                            'domain': domain,
                            'raw_data': {
                                'port': port,
                                'exposure_count': results['total'],
                                'severity': 'HIGH' if port in ['3389', '6379', '21', '23'] else 'MEDIUM'
                            },
                            'priority_score': 0.8,
                            'campaign_type': 'network_security_assessment'
                        }
                        signals.append(signal)
                        
                except Exception as e:
                    logger.warning(f"Error scanning port {port} for {domain}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in critical port scan for {domain}: {e}")
            
        return signals

    def get_shodan_host_info(self, ip: str) -> Dict:
        """Get detailed host information from Shodan"""
        try:
            self.check_rate_limit()
            host_info = self.api.host(ip)
            self.rate_limit_count += 1
            
            return {
                'ip': ip,
                'country': host_info.get('country_name', 'Unknown'),
                'city': host_info.get('city', 'Unknown'),
                'organization': host_info.get('org', 'Unknown'),
                'asn': host_info.get('asn', 'Unknown'),
                'ports': len(host_info.get('ports', [])),
                'vulns': len(host_info.get('vulns', [])),
                'software': [item.get('product', '') for item in host_info.get('data', [])],
                'last_update': host_info.get('last_update', 'Unknown')
            }
            
        except Exception as e:
            logger.error(f"Error getting Shodan host info for {ip}: {e}")
            return {'error': str(e)}

    def check_vulnerability_database(self, software_name: str, version: str = None) -> List[Dict]:
        """Check Shodan for known vulnerabilities"""
        signals = []
        
        try:
            self.check_rate_limit()
            
            search_query = f"{software_name}"
            if version:
                search_query += f" {version}"
                
            results = self.api.search(search_query, facets={'vuln': 10})
            self.rate_limit_count += 1
            
            vulns = [item['value'] for item in results.get('facets', {}).get('vuln', [])]
            
            if vulns:
                signal = {
                    'signal_type': 'vulnerable_software_detected',
                    'signal_date': datetime.utcnow().isoformat(),
                    'signal_strength': 0.9,
                    'source': 'shodan_vuln_db',
                    'raw_data': {
                        'software': software_name,
                        'version': version,
                        'vulnerabilities': vulns[:5],  # Top 5 vulns
                        'total_vulns': len(vulns)
                    },
                    'priority_score': 0.9,
                    'campaign_type': 'vulnerability_response'
                }
                signals.append(signal)
                
        except Exception as e:
            logger.error(f"Error checking vulnerability database: {e}")
            
        return signals

def collect_all_threats(self, domain: str = None) -> List[Dict]:
    """Collect all Shodan-based threat signals for a domain"""
    if not domain:
        return []
        
    all_signals = []
    
    # Domain exposure analysis  
    company_data = {'domain': domain, 'company_name': domain}
    all_signals.extend(self.analyze_domain_exposure(company_data))
    
    # Critical port scan
    all_signals.extend(self.scan_critical_ports(domain))
    
    return all_signals
