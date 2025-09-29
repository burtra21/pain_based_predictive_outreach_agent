"""
Enhanced Reactive Analyzer API
Handles Clay-enriched company data for pain-based analysis
"""

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, List, Optional
import hmac
import hashlib
import json
import time
from datetime import datetime
import requests
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

# Add src to path for local imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from collectors.company_analyzer import CompanyAnalyzer
from collectors.smart_tech_analyzer import SmartTechStackAnalyzer
from clay_client import ClayClient
from config.settings import config

app = FastAPI(
    title="Enhanced BTA Reactive Analyzer API",
    description="API for analyzing Clay-enriched company data and generating pain-based signals",
    version="2.0.0"
)

# Initialize ClayClient and Collectors
clay_client = ClayClient(api_key=config.CLAY_API_KEY, workspace=config.CLAY_WORKSPACE)
company_analyzer = CompanyAnalyzer(clay_client)
smart_tech_analyzer = SmartTechStackAnalyzer(clay_client, builtwith_api_key=config.WAPPALYZER_API_KEY)

class ClayEnrichedCompany(BaseModel):
    """Clay-enriched company data structure"""
    
    # Core company data
    company_name: str
    companyId: Optional[int] = None
    websiteUrl: Optional[str] = None
    industry: Optional[str] = None
    universalName: Optional[str] = None
    
    # Business details
    employeeCount: Optional[int] = None
    employeeCountRange: Optional[Dict] = None
    foundedOn: Optional[Dict] = None
    description: Optional[str] = None
    tagline: Optional[str] = None
    
    # Location data
    locations: Optional[List[Dict]] = None
    headquarter: Optional[Dict] = None
    
    # Specializations
    specialities: Optional[List[str]] = None
    
    # Social/External data
    followerCount: Optional[int] = None
    linkedinUrl: Optional[str] = None
    
    # Enrichment flags
    needs_pain_analysis: bool = True
    priority_score: Optional[float] = None
    
    # Existing contact data (if already enriched)
    contact_emails: Optional[List[str]] = None
    contact_phones: Optional[List[str]] = None
    industry_contacts: Optional[Dict] = None

class TechStackAnalysis(BaseModel):
    """Technology stack analysis from BuiltWith"""
    domain: str
    source: str
    summary: str
    risk_assessment: Dict
    vulnerabilities: Dict
    outreach_priority: Dict
    detection_capabilities: Dict
    
    # Pain signals derived from tech stack
    pain_signals: Optional[List[Dict]] = None
    dwell_time_risk: Optional[str] = None
    ransomware_vulnerability: Optional[bool] = None

class EnrichedAnalysisRequest(BaseModel):
    """Request containing Clay-enriched data"""
    companies: List[ClayEnrichedCompany]
    include_tech_analysis: bool = True
    include_contact_enrichment: bool = False
    priority_filter: Optional[float] = 0.7  # Only analyze companies above this score
    analysis_options: Optional[Dict] = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "enhanced_features": ["Clay Integration", "Tech Stack Analysis", "Priority Scoring"]
    }

@app.get("/diagnostics")
async def system_diagnostics():
    """Diagnostic information for troubleshooting"""
    diagnostics = {
        "timestamp": datetime.utcnow().isoformat(),
        "environment_variables": {
            "CLAY_API_KEY": "✅ Configured" if config.CLAY_API_KEY else "❌ Missing",
            "CLAY_WORKSPACE": "✅ Configured" if config.CLAY_WORKSPACE else "❌ Missing", 
            "CLAY_WEBHOOK_URL": "✅ Configured" if config.CLAY_WEBHOOK_URL else "❌ Missing",
            "HIBP_API_KEY": "✅ Configured" if config.HIBP_API_KEY else "❌ Missing",
            "SERPAPI_API_KEY": "✅ Configured" if config.SERPAPI_API_KEY else "❌ Missing",
            "SHODAN_API_KEY": "✅ Configured" if config.SHODAN_API_KEY else "❌ Missing",
        },
        "collectors": {
            "shodan_available": company_analyzer.shodan_monitor is not None,
            "analysis_methods": company_analyzer.analysis_methods
        }
    }
    return diagnostics

@app.post("/clay-webhook-trigger", response_model=Dict)
async def clay_webhook_trigger(request_data: Dict):
    """OPTIMIZED endpoint for Clay webhook triggers - designed for speed under 15 seconds"""
    logger.info(f"Received Clay webhook trigger with data keys: {list(request_data.keys())}")
    start_time = time.time()
    
    try:
        # Extract company data from webhook payload
        company_data = request_data.get('company_data', request_data)
        
        # Convert to ClayEnrichedCompany format
        enriched_data = ClayEnrichedCompany(**company_data)
        
        # FAST ANALYSIS - Only critical signals within 15 second timeout
        domain = extract_domain_from_url(enriched_data.websiteUrl)
        if not domain:
            return {
                "success": True,
                "message": "Clay webhook trigger processed successfully",
                "analysis_result": {
                    "company_name": enriched_data.company_name,
                    "domain": domain,
                    "signals_found": 0,
                    "signals": [],
                    "analysis_time": time.time() - start_time,
                    "priority_score": 0.0,
                    "data_richness": "basic",
                    "success": True
                }
            }
        
        # Convert to analysis format quickly
        company_dict = {
            'company_name': enriched_data.company_name,
            'domain': domain,
            'industry': enriched_data.industry,
            'employee_count': enriched_data.employeeCount,
            'location': extract_location(enriched_data.headquarter),
            'company_size': categorize_company_size(enriched_data.employeeCount)
        }
        
        signals = []
        
        # Track all analysis methods for comprehensive reporting
        analysis_results = {
            "hibp_breach_check": {"executed": False, "signals": 0, "status": "skipped"},
            "serpapi_breach_search": {"executed": False, "signals": 0, "status": "skipped"},
            "shodan_network_exposure": {"executed": False, "signals": 0, "status": "skipped"},
            "tech_stack_analysis": {"executed": False, "signals": 0, "status": "skipped"}
        }
        
        # FASTEST checks only (under 5 seconds each)
        try:
            # HIBP check (fast)
            hibp_signals = company_analyzer.check_hibp_breaches(company_dict)
            signals.extend(hibp_signals)
            analysis_results["hibp_breach_check"] = {"executed": True, "signals": len(hibp_signals), "status": "success"}
            logger.info(f"HIBP check completed for {enriched_data.company_name}: {len(hibp_signals)} signals")
        except Exception as e:
            analysis_results["hibp_breach_check"] = {"executed": True, "signals": 0, "status": f"error: {str(e)}"}
            logger.warning(f"HIBP check failed for {enriched_data.company_name}: {e}")
        
        try:
            # SERPAPI breach search (fast)
            serpapi_signals = company_analyzer.check_breach_mentions_serpapi(company_dict)
            signals.extend(serpapi_signals)
            analysis_results["serpapi_breach_search"] = {"executed": True, "signals": len(serpapi_signals), "status": "success"}
            logger.info(f"SERPAPI check completed for {enriched_data.company_name}: {len(serpapi_signals)} signals")
        except Exception as e:
            analysis_results["serpapi_breach_search"] = {"executed": True, "signals": 0, "status": f"error: {str(e)}"}
            logger.warning(f"SERPAPI check failed for {enriched_data.company_name}: {e}")
        
        # SHODAN network exposure check (add to ensure it's included)
        if company_analyzer.shodan_monitor:
            try:
                shodan_signals = company_analyzer.check_shodan_exposures(company_dict)
                signals.extend(shodan_signals)
                analysis_results["shodan_network_exposure"] = {"executed": True, "signals": len(shodan_signals), "status": "success"}
                logger.info(f"Shodan check completed for {enriched_data.company_name}: {len(shodan_signals)} signals")
            except Exception as e:
                analysis_results["shodan_network_exposure"] = {"executed": True, "signals": 0, "status": f"error: {str(e)}"}
                logger.warning(f"Shodan check failed for {enriched_data.company_name}: {e}")
        else:
            analysis_results["shodan_network_exposure"]["status"] = "skipped: API key not configured"
            logger.info(f"Shodan not available for {enriched_data.company_name} (API key not configured)")
        
        # Quick tech gap detection (if time permits)
        if time.time() - start_time < 5.0:  # Only if under 5 seconds
            try:
                tech_signals = company_analyzer.analyze_technology_stack(company_dict)
                signals.extend(tech_signals)
                analysis_results["tech_stack_analysis"] = {"executed": True, "signals": len(tech_signals), "status": "success"}
                logger.info(f"Tech analysis completed for {enriched_data.company_name}: {len(tech_signals)} signals")
            except Exception as e:
                analysis_results["tech_stack_analysis"] = {"executed": True, "signals": 0, "status": f"error: {str(e)}"}
                logger.warning(f"Tech analysis failed for {enriched_data.company_name}: {e}")
        else:
            analysis_results["tech_stack_analysis"]["status"] = "skipped: timeout constraint"
        
        # Calculate priority score
        priority_score = 0.0
        for signal in signals:
            priority_score = max(priority_score, signal.get('signal_strength', 0.5))
        
        analysis_time = time.time() - start_time
        
        logger.info(f"Fast analysis complete for {enriched_data.company_name}: {len(signals)} signals in {analysis_time:.2f}s")

        return {
            "success": True,
            "message": "Clay webhook trigger processed successfully",
            "analysis_result": {
                "company_name": enriched_data.company_name,
                "domain": domain,
                "signals_found": len(signals),
                "signals": signals,
                "analysis_time": analysis_time,
                "priority_score": priority_score,
                "data_richness": "moderate",
                "success": True,
                "analysis_methods": analysis_results
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing Clay webhook trigger: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to process Clay webhook trigger"
        }

@app.post("/analyze-enriched-company")
async def analyze_enriched_company(company: ClayEnrichedCompany):
    """Analyze a single Clay-enriched company"""
    logger.info(f"Analyzing enriched company: {company.company_name}")
    start_time = time.time()
    
    try:
        # Convert Clay data to our standard format
        company_dict = {
            'company_name': company.company_name,
            'domain': extract_domain_from_url(company.websiteUrl),
            'industry': company.industry,
            'employee_count': company.employeeCount,
            'location': extract_location(company.headquarter),
            'founded_year': extract_founded_year(company.foundedOn),
            'company_size': categorize_company_size(company.employeeCount),
            'description': company.description,
            'linkedin_url': company.linkedinUrl,
            'specialities': company.specialities or []
        }
        
        # Calculate priority score based on data richness
        priority_score = calculate_priority_score(company_dict)
        company_dict['priority_score'] = priority_score
        
        logger.info(f"Priority score for {company.company_name}: {priority_score}")
        
        # Run pain signal analysis
        signals = company_analyzer.analyze_single_company(company_dict)
        
        # Enhance signals with Clay-specific context
        enhanced_signals = enhance_signals_with_clay_data(signals, company)
        
        analysis_time = time.time() - start_time
        
        return {
            "success": True,
            "company_name": company.company_name,
            "domain": company_dict.get('domain', ''),
            "priority_score": priority_score,
            "signals_found": len(enhanced_signals),
            "signals": enhanced_signals,
            "analysis_time": analysis_time,
            "data_richness": assess_data_richness(company)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing enriched company {company.company_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-enriched-batch")
async def analyze_enriched_batch(request: EnrichedAnalysisRequest):
    """Analyze a batch of Clay-enriched companies"""
    logger.info(f"Processing batch of {len(request.companies)} enriched companies")
    start_time = time.time()
    
    # Filter by priority if specified
    filtered_companies = request.companies
    if request.priority_filter:
        filtered_companies = [
            c for c in request.companies 
            if calculate_priority_score_from_clay(c) >= request.priority_filter
        ]
    
    logger.info(f"Processing {len(filtered_companies)} companies after priority filtering")
    
    all_results = []
    
    # Process companies in batches of 10
    batch_size = 10
    for i in range(0, len(filtered_companies), batch_size):
        batch = filtered_companies[i:i + batch_size]
        
        for company in batch:
            try:
                # Convert Clay data to analysis format
                company_dict = convert_clay_to_analysis(company)
                
                # Run analysis
                signals = company_analyzer.analyze_single_company(company_dict)
                
                # Add tech stack analysis if requested
                if request.include_tech_analysis and company.websiteUrl:
                    tech_signals = smart_tech_analyzer.analyze_tech_stack(company_dict)
                    if tech_signals and tech_signals.get('signals'):
                        signals.extend(tech_signals['signals'])
                
                # Enhance signals
                enhanced_signals = enhance_signals_with_clay_data(signals, company)
                
                result = {
                    "company_name": company.company_name,
                    "domain": company_dict.get('domain', ''),
                    "signals": enhanced_signals,
                    "priority_score": company_dict.get('priority_score', 0.5),
                    "data_richness": assess_data_richness(company)
                }
                
                all_results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing company {company.company_name}: {e}")
                continue
        
        # Rate limiting between batches
        if i + batch_size < len(filtered_companies):
            time.sleep(1)
    
    # Send batch results to Clay webhook
    batch_payload = {
        "event_type": "enriched_batch_analysis_complete",
        "timestamp": datetime.utcnow().isoformat(),
        "source": "enhanced_api",
        "data": {
            "batch_info": {
                "total_companies": len(request.companies),
                "filtered_companies": len(filtered_companies),
                "processed_companies": len(all_results),
                "priority_threshold": request.priority_filter
            },
            "results": all_results
        }
    }
    
    try:
        clay_result = clay_client.trigger_webhook(config.CLAY_WEBHOOK_URL, batch_payload)
        logger.info(f"Batch analysis sent to Clay: {clay_result}")
    except Exception as e:
        logger.error(f"Error sending batch to Clay webhook: {e}")
    
    total_time = time.time() - start_time
    
    return {
        "success": True,
        "message": f"Processed {len(all_results)} enriched companies",
        "summary": {
            "original_count": len(request.companies),
            "filtered_count": len(filtered_companies),
            "processed_count": len(all_results),
            "total_signals": sum(len(r['signals']) for r in all_results),
            "processing_time": total_time,
            "priority_threshold": request.priority_filter
        },
        "results": all_results
    }

@app.post("/analyze-tech-stack-with-clay")
async def analyze_tech_stack_with_clay_data(
    company: ClayEnrichedCompany,
    tech_stack: Optional[TechStackAnalysis] = None
):
    """Analyze tech stack using Clay-enriched company data"""
    logger.info(f"Analyzing tech stack for enriched company: {company.company_name}")
    
    try:
        # Convert Clay data
        company_dict = convert_clay_to_analysis(company)
        
        # Run tech analysis
        tech_analysis = smart_tech_analyzer.analyze_tech_stack(company_dict)
        
        # Enhance with tech stack data if provided
        if tech_stack:
            tech_analysis = enhance_with_builtwith_data(tech_analysis, tech_stack)
        
        # Calculate enhanced pain signals
        pain_signals = generate_tech_pain_signals(company_dict, tech_analysis, tech_stack)
        
        # Send results to Clay
        payload = {
            "event_type": "enhanced_tech_analysis",
            "timestamp": datetime.utcnow().isoformat(),
            "source": "enhanced_api",
            "data": {
                "company": company.dict(),
                "tech_analysis": tech_analysis,
                "pain_signals": pain_signals,
                "risk_assessment": tech_stack.risk_assessment if tech_stack else {}
            }
        }
        
        clay_result = clay_client.trigger_webhook(config.CLAY_WEBHOOK_URL, payload)
        
        return {
            "success": True,
            "company_name": company.company_name,
            "domain": company_dict.get('domain', ''),
            "tech_analysis": tech_analysis,
            "pain_signals": pain_signals,
            "risk_score": extract_risk_score(tech_analysis),
            "clay_integration": clay_result
        }
        
    except Exception as e:
        logger.error(f"Error in-tech stack analysis for {company.company_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions

def extract_domain_from_url(url: Optional[str]) -> str:
    """Extract domain from Clay website URL"""
    if not url:
        return ""
    
    # Remove protocol and www
    domain = url.replace('https://www.', '').replace('http://www.', '')
    domain = domain.replace('https://', '').replace('http://', '')
    
    # Remove trailing slash
    domain = domain.rstrip('/')
    
    return domain

def extract_location(headquarters: Optional[Dict]) -> str:
    """Extract location string from headquarters data"""
    if not headquarters:
        return ""
    
    parts = []
    if headquarters.get('city'):
        parts.append(headquarters['city'])
    if headquarters.get('geographicArea'):
        parts.append(headquarters['geographicArea'])
    if headquarters.get('country'):
        parts.append(headquarters['country'])
    
    return ', '.join(parts)

def extract_founded_year(founded_date: Optional[Dict]) -> Optional[int]:
    """Extract founded year from Clay date structure"""
    if not founded_date:
        return None
    
    return founded_date.get('year')

def categorize_company_size(employee_count: Optional[int]) -> str:
    """Categorize company size for analysis"""
    if not employee_count:
        return "unknown"
    
    if employee_count < 50:
        return "small"
    elif employee_count < 200:
        return "medium"
    elif employee_count < 1000:
        return "large"
    else:
        return "enterprise"

def calculate_priority_score(company_dict: Dict) -> float:
    """Calculate priority score based on data richness"""
    score = 0.5  # Base score
    
    # Company name (required)
    if company_dict.get('company_name'):
        score += 0.1
    
    # Domain (high value)
    if company_dict.get('domain'):
        score += 0.15
    
    # Employee count (valuable for targeting)
    if company_dict.get('employee_count'):
        score += 0.1
    
    # Industry (important for analysis)
    if company_dict.get('industry'):
        score += 0.1
    
    # Location (good for regional campaigns)
    if company_dict.get('location'):
        score += 0.05
    
    # LinkedIn data (social validation)
    if company_dict.get('linkedin_url'):
        score += 0.05
    
    # Company description (context for pain signals)
    if company_dict.get('description'):
        score += 0.05
    
    return min(score, 1.0)

def calculate_priority_score_from_clay(company: ClayEnrichedCompany) -> float:
    """Calculate priority directly from Clay company object"""
    score = 0.5
    
    if company.company_name:
        score += 0.1
    if company.websiteUrl:
        score += 0.15
    if company.employeeCount:
        score += 0.1
    if company.industry:
        score += 0.1
    if company.headquarter:
        score += 0.05
    if company.linkedinUrl:
        score += 0.05
    if company.description:
        score += 0.05
    
    return min(score, 1.0)

def convert_clay_to_analysis(company: ClayEnrichedCompany) -> Dict:
    """Convert Clay company data to our analysis format"""
    return {
        'company_name': company.company_name,
        'domain': extract_domain_from_url(company.websiteUrl),
        'industry': company.industry,
        'employee_count': company.employeeCount,
        'location': extract_location(company.headquarter),
        'founded_year': extract_founded_year(company.foundedOn),
        'company_size': categorize_company_size(company.employeeCount),
        'description': company.description,
        'linkedin_url': company.linkedinUrl,
        'specialities': company.specialities or [],
        'priority_score': calculate_priority_score_from_clay(company)
    }

def enhance_signals_with_clay_data(signals: List[Dict], company: ClayEnrichedCompany) -> List[Dict]:
    """Enhance pain signals with Clay-specific context"""
    enhanced = []
    
    for signal in signals:
        # Add Clay enrichment context
        if company.employeeCount:
            signal['company_size'] = categorize_company_size(company.employeeCount)
        
        if company.industry:
            signal['industry_context'] = company.industry
        
        if company.linkedinUrl:
            signal['linkedin_url'] = company.linkedinUrl
        
        if company.followerCount:
            signal['social_validation'] = {
                'linkedin_followers': company.followerCount,
                'social_strength': 'high' if company.followerCount > 10000 else 'medium'
            }
        
        # Increase signal strength for well-enriched companies
        if company.employeeCount and company.foundedOn:
            signal['signal_strength'] = min(signal.get('signal_strength', 0.5) + 0.1, 1.0)
        
        enhanced.append(signal)
    
    return enhanced

def assess_data_richness(company: ClayEnrichedCompany) -> str:
    """Assess how rich the Clay data is"""
    rich_fields = 0
    
    if company.company_name: rich_fields += 1
    if company.websiteUrl: rich_fields += 1
    if company.employeeCount: rich_fields += 1
    if company.industry: rich_fields += 1
    if company.description: rich_fields += 1
    if company.headquarter: rich_fields += 1
    if company.linkedinUrl: rich_fields += 1
    if company.foundedOn: rich_fields += 1
    if company.specialities: rich_fields += 1
    
    if rich_fields >= 7:
        return "very_rich"
    elif rich_fields >= 5:
        return "rich"
    elif rich_fields >= 3:
        return "moderate"
    else:
        return "minimal"

def enhance_with_builtwith_data(analysis: Dict, tech_stack: TechStackAnalysis) -> Dict:
    """Enhance analysis with BuiltWith tech stack data"""
    enhancement = {
        "builtwith_data": {
            "risk_level": tech_stack.risk_assessment.get('Risk_Level', 'UNKNOWN'),
            "security_gaps": tech_stack.vulnerabilities.get('MISSING_TOOLS', []),
            "exploit_vectors": tech_stack.vulnerabilities.get('EXPLOIT_VECTORS', []),
            "detection_capabilities": tech_stack.detection_capabilities,
            "dwell_time_risk": tech_stack.risk_assessment.get('Dwell_Time_Risk', 'UNKNOWN'),
            "ransomware_vulnerable": tech_stack.risk_assessment.get('Ransomware_Risk', False)
        }
    }
    
    analysis.update(enhancement)
    return analysis

def generate_tech_pain_signals(company_dict: Dict, tech_analysis: Dict, tech_stack: Optional[TechStackAnalysis]) -> List[Dict]:
    """Generate pain signals from tech stack analysis"""
    signals = []
    
    # Signal based on missing security tools
    if tech_stack and tech_stack.vulnerabilities.get('MISSING_TOOLS'):
        signal = {
            'company_name': company_dict['company_name'],
            'domain': company_dict.get('domain', ''),
            'signal_type': 'critical_security_gaps',
            'signal_date': datetime.utcnow().isoformat(),
            'signal_strength': 0.9,
            'raw_data': {
                'missing_tools': tech_stack.vulnerabilities['MISSING_TOOLS'],
                'risk_level': tech_stack.risk_assessment.get('Risk_Level', 'HIGH'),
                'dwell_time': tech_stack.risk_assessment.get('Dwell_Time_Risk', 'EXTREME'),
                'detection_method': 'builtwith_analysis'
            },
            'source': 'enhanced_tech_analysis'
        }
        signals.append(signal)
    
    # Signal based on ransomware vulnerability
    if tech_stack and tech_stack.risk_assessment.get('Ransomware_Risk'):
        signal = {
            'company_name': company_dict['company_name'],
            'domain': company_dict.get('domain', ''),
            'signal_type': 'ransomware_vulnerability_detected',
            'signal_date': datetime.utcnow().isoformat(),
            'signal_strength': 0.95,
            'raw_data': {
                'vulnerability_confirmed': True,
                'missing_protections': tech_stack.vulnerabilities.get('MISSING_TOOLS', []),
                'outreach_message': tech_stack.outreach_priority.get('Recommended_Message', 'urgent_security_alert'),
                'detection_method': 'builtwith_vulnerability_scan'
            },
            'source': 'enhanced_tech_analysis'
        }
        signals.append(signal)
    
    return signals

def extract_risk_score(analysis: Dict) -> float:
    """Extract risk score from analysis"""
    if 'builtwith_data' in analysis:
        risk_level = analysis['builtwith_data']['risk_level']
        risk_map = {'CRITICAL': 0.95, 'HIGH': 0.8, 'MEDIUM': 0.6, 'LOW': 0.3}
        return risk_map.get(risk_level, 0.5)
    
    return analysis.get('security_analysis', {}).get('gap_score', 0.5)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
