#!/usr/bin/env python3
"""
Reactive Analyzer API
HTTP API for receiving company data from Clay and running reactive analysis
"""

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import hmac
import hashlib
import json
import sys
import os
from datetime import datetime
import logging

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from clay_client import ClayClient
from collectors.company_analyzer import CompanyAnalyzer
from collectors.smart_tech_analyzer import SmartTechStackAnalyzer
from config.settings import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Reactive Analyzer API", version="1.0.0")

# Initialize components
clay_client = ClayClient(config.CLAY_API_KEY, config.CLAY_WORKSPACE)
company_analyzer = CompanyAnalyzer(clay_client)
tech_analyzer = SmartTechStackAnalyzer(clay_client)

class CompanyData(BaseModel):
    """Company data model for reactive analysis"""
    company_name: str
    domain: str
    industry: Optional[str] = None
    employee_count: Optional[int] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    data_source: Optional[str] = "clay_enrichment"
    
    # Clay-enriched fields (optional)
    builtwith_data: Optional[Dict] = None
    contact_data: Optional[Dict] = None
    company_info: Optional[Dict] = None

class BatchCompanyRequest(BaseModel):
    """Batch request for multiple companies"""
    companies: List[CompanyData]
    analysis_options: Optional[Dict] = Field(default_factory=dict)
    webhook_url: Optional[str] = None

class AnalysisResponse(BaseModel):
    """Response model for analysis results"""
    success: bool
    message: str
    companies_processed: int
    signals_found: int
    analysis_id: str
    results: Optional[Dict] = None

class SingleCompanyResponse(BaseModel):
    """Response for single company analysis"""
    success: bool
    company_name: str
    domain: str
    signals_found: int
    signals: List[Dict]
    analysis_time: float

@app.post("/analyze-company", response_model=SingleCompanyResponse)
async def analyze_single_company(company: CompanyData):
    """Analyze a single company for pain signals"""
    start_time = datetime.utcnow()
    
    try:
        logger.info(f"Analyzing single company: {company.company_name}")
        
        # Convert to dict for analysis
        company_dict = company.dict()
        
        # Run analysis
        signals = company_analyzer.analyze_single_company(company_dict)
        
        # Calculate analysis time
        analysis_time = (datetime.utcnow() - start_time).total_seconds()
        
        return SingleCompanyResponse(
            success=True,
            company_name=company.company_name,
            domain=company.domain,
            signals_found=len(signals),
            signals=signals,
            analysis_time=analysis_time
        )
        
    except Exception as e:
        logger.error(f"Error analyzing company {company.company_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-batch", response_model=AnalysisResponse)
async def analyze_batch_companies(
    request: BatchCompanyRequest, 
    background_tasks: BackgroundTasks
):
    """Analyze a batch of companies for pain signals"""
    analysis_id = f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        logger.info(f"Starting batch analysis {analysis_id} for {len(request.companies)} companies")
        
        # Add to background tasks for processing
        background_tasks.add_task(
            process_batch_analysis,
            request.companies,
            analysis_id,
            request.analysis_options,
            request.webhook_url
        )
        
        return AnalysisResponse(
            success=True,
            message=f"Batch analysis {analysis_id} started",
            companies_processed=len(request.companies),
            signals_found=0,  # Will be updated by background task
            analysis_id=analysis_id
        )
        
    except Exception as e:
        logger.error(f"Error starting batch analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-tech-stack")
async def analyze_tech_stack(company: CompanyData):
    """Analyze technology stack for a single company"""
    try:
        logger.info(f"Analyzing tech stack for: {company.company_name}")
        
        # Convert to dict for analysis
        company_dict = company.dict()
        
        # Run tech stack analysis
        tech_analysis = tech_analyzer.analyze_tech_stack(company_dict)
        
        # Send results to Clay webhook
        if tech_analysis and tech_analysis.get('signals'):
            clay_payload = {
                "event_type": "tech_analysis_complete",
                "timestamp": datetime.utcnow().isoformat(),
                "source": "reactive_api",
                "data": {
                    "company": company.dict(),
                    "tech_analysis": tech_analysis,
                    "signals": tech_analysis.get('signals', [])
                }
            }
            
            clay_result = clay_client.trigger_webhook(config.CLAY_WEBHOOK_URL, clay_payload)
            logger.info(f"Tech analysis sent to Clay: {clay_result}")
        
        return {
            "success": True,
            "company_name": company.company_name,
            "domain": company.domain,
            "tech_analysis": tech_analysis
        }
        
    except Exception as e:
        logger.error(f"Error analyzing tech stack for {company.company_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/analysis-methods")
async def get_analysis_methods():
    """Get available analysis methods"""
    return {
        "company_analysis_methods": [
            "breach_history_check",
            "job_posting_analysis", 
            "technology_stack_analysis",
            "insurance_risk_assessment",
            "compliance_vulnerability_check"
        ],
        "tech_analysis_methods": [
            "security_tools_detection",
            "compliance_tools_detection",
            "tech_gap_analysis",
            "security_headers_check"
        ]
    }

async def process_batch_analysis(
    companies: List[CompanyData],
    analysis_id: str,
    options: Dict,
    webhook_url: Optional[str]
):
    """Background task to process batch analysis"""
    total_signals = 0
    processed_companies = 0
    
    try:
        logger.info(f"Processing batch {analysis_id} with {len(companies)} companies")
        
        for company in companies:
            try:
                # Convert to dict for analysis
                company_dict = company.dict()
                
                # Run analysis
                signals = company_analyzer.analyze_single_company(company_dict)
                total_signals += len(signals)
                processed_companies += 1
                
                logger.info(f"Processed {company.company_name}: {len(signals)} signals")
                
            except Exception as e:
                logger.error(f"Error processing {company.company_name}: {e}")
                continue
        
        # Send results to Clay webhook
        clay_payload = {
            "event_type": "batch_analysis_complete",
            "timestamp": datetime.utcnow().isoformat(),
            "source": "reactive_api",
            "data": {
                "analysis_id": analysis_id,
                "companies_processed": processed_companies,
                "signals_found": total_signals,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        try:
            clay_result = clay_client.trigger_webhook(config.CLAY_WEBHOOK_URL, clay_payload)
            logger.info(f"Batch analysis sent to Clay: {clay_result}")
        except Exception as e:
            logger.error(f"Error sending to Clay webhook: {e}")
        
        # Also send to custom webhook if provided
        if webhook_url:
            await send_results_to_webhook(webhook_url, {
                "analysis_id": analysis_id,
                "companies_processed": processed_companies,
                "signals_found": total_signals,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        logger.info(f"Batch {analysis_id} complete: {processed_companies} companies, {total_signals} signals")
        
    except Exception as e:
        logger.error(f"Error in batch processing {analysis_id}: {e}")

async def send_results_to_webhook(webhook_url: str, data: Dict):
    """Send analysis results to webhook"""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=data) as response:
                if response.status == 200:
                    logger.info(f"Results sent to webhook: {webhook_url}")
                else:
                    logger.error(f"Webhook failed: {response.status}")
    except Exception as e:
        logger.error(f"Error sending to webhook: {e}")

def verify_clay_signature(body: bytes, signature: str) -> bool:
    """Verify Clay webhook signature"""
    try:
        expected_signature = hmac.new(
            config.CLAY_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        logger.error(f"Error verifying signature: {e}")
        return False

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
