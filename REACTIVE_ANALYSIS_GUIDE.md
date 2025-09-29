# Reactive Analysis System - Complete Guide

## Overview

The reactive analysis system is designed to analyze existing companies in your Clay database for pain signals and generate targeted outreach campaigns. This system works in parallel with the proactive collectors.

## System Architecture

```
Clay Database → HTTP API → Python Analysis → Pain Signals → Clay Webhook → Campaigns
```

## Data Flow

### 1. **Clay Enrichment** (Recommended)
- Enrich companies in Clay with basic data (contacts, company info, etc.)
- Send enriched data to Python API for analysis
- Python focuses on pain signal detection

### 2. **Python Analysis** (Core)
- Receives company data via HTTP API
- Runs 5 analysis methods per company
- Generates pain signals and scores
- Sends results back to Clay

### 3. **Campaign Generation** (Automated)
- Clay processes pain signals
- Generates personalized campaigns
- Queues for outreach

## API Endpoints

### Base URL: `http://your-server:8001`

#### 1. **Single Company Analysis**
```http
POST /analyze-company
Content-Type: application/json

{
  "company_name": "Example Corp",
  "domain": "example.com",
  "industry": "Healthcare",
  "employee_count": 500,
  "location": "San Francisco, CA",
  "linkedin_url": "https://linkedin.com/company/example-corp",
  "data_source": "clay_enrichment",
  "builtwith_data": {
    "technologies": ["react", "aws", "salesforce"]
  },
  "contact_data": {
    "ciso_email": "ciso@example.com",
    "ciso_name": "John Smith"
  }
}
```

**Response:**
```json
{
  "success": true,
  "company_name": "Example Corp",
  "domain": "example.com",
  "signals_found": 3,
  "signals": [
    {
      "signal_type": "security_job_postings",
      "signal_strength": 0.6,
      "raw_data": {
        "job_count": 3,
        "search_term": "Example Corp CISO"
      }
    }
  ],
  "analysis_time": 2.5
}
```

#### 2. **Batch Company Analysis**
```http
POST /analyze-batch
Content-Type: application/json

{
  "companies": [
    {
      "company_name": "Company 1",
      "domain": "company1.com"
    },
    {
      "company_name": "Company 2", 
      "domain": "company2.com"
    }
  ],
  "analysis_options": {
    "include_tech_analysis": true,
    "max_signals_per_company": 10
  },
  "webhook_url": "https://your-clay-webhook.com/results"
}
```

#### 3. **Tech Stack Analysis**
```http
POST /analyze-tech-stack
Content-Type: application/json

{
  "company_name": "Example Corp",
  "domain": "example.com",
  "builtwith_data": {
    "technologies": ["react", "aws", "salesforce"]
  }
}
```

#### 4. **Health Check**
```http
GET /health
```

#### 5. **Available Methods**
```http
GET /analysis-methods
```

## Analysis Methods

### 1. **Breach History Check**
- **Method**: Google News search for breach mentions
- **Signal**: `breach_mention_detected`
- **Strength**: 0.8
- **Keywords**: "data breach", "security incident", "cyber attack"

### 2. **Job Posting Analysis**
- **Method**: LinkedIn Jobs search for security roles
- **Signal**: `security_job_postings`
- **Strength**: 0.3 + (job_count × 0.1)
- **Keywords**: "CISO", "security director", "cybersecurity"

### 3. **Technology Stack Analysis**
- **Method**: BuiltWith data analysis for security gaps
- **Signal**: `security_tech_gaps`
- **Strength**: 0.2 per gap
- **Checks**: MDR, SIEM, EDR, firewall, email security

### 4. **Insurance Risk Assessment**
- **Method**: Risk score calculation
- **Signal**: `high_insurance_risk`
- **Strength**: Calculated risk score
- **Factors**: Industry, size, compliance requirements

### 5. **Compliance Vulnerability Check**
- **Method**: Compliance issue identification
- **Signal**: `compliance_vulnerability`
- **Strength**: 0.3 per issue
- **Checks**: HIPAA, SOX, PCI, GDPR

## Data Enrichment Strategy

### **Clay Should Enrich:**
- **Company Information**: Name, domain, industry, employee count
- **Contact Data**: CISO email, security team contacts
- **Basic Tech Stack**: BuiltWith data, website technologies
- **Company Details**: Location, LinkedIn URL, company size

### **Python Should Analyze:**
- **Pain Signals**: Breach mentions, job postings, tech gaps
- **Risk Assessment**: Insurance risk, compliance issues
- **Signal Scoring**: EDP scores, campaign recommendations
- **Advanced Analysis**: Security tool gaps, compliance vulnerabilities

## Clay Integration

### **1. HTTP Request Node in Clay**
```javascript
// Clay HTTP Request configuration
{
  "url": "http://your-server:8001/analyze-company",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "company_name": "{{company_name}}",
    "domain": "{{domain}}",
    "industry": "{{industry}}",
    "employee_count": "{{employee_count}}",
    "location": "{{location}}",
    "linkedin_url": "{{linkedin_url}}",
    "builtwith_data": "{{builtwith_data}}",
    "contact_data": "{{contact_data}}"
  }
}
```

### **2. Webhook Response Handling**
```javascript
// Process analysis results
if (response.success) {
  // Add pain signals to pain_signals table
  for (signal of response.signals) {
    addToTable("pain_signals", {
      domain: signal.domain,
      signal_type: signal.signal_type,
      signal_strength: signal.signal_strength,
      raw_data: signal.raw_data,
      source: "reactive_analysis"
    });
  }
  
  // Update company as analyzed
  updateTable("company_universe", {
    domain: response.domain,
    analyzed: true,
    last_analysis: new Date().toISOString()
  });
}
```

## n8n Workflow Integration

### **Workflow Steps:**
1. **Trigger**: New company added to company_universe
2. **Enrichment**: Clay enrichment (contacts, tech stack)
3. **Analysis**: HTTP request to Python API
4. **Processing**: Parse analysis results
5. **Storage**: Add pain signals to pain_signals table
6. **Campaign**: Generate campaign if signals found
7. **Queue**: Add to outreach queue

### **n8n Node Configuration:**
```json
{
  "nodes": [
    {
      "name": "Company Added Trigger",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "company-added",
        "httpMethod": "POST"
      }
    },
    {
      "name": "Analyze Company",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://your-server:8001/analyze-company",
        "method": "POST",
        "body": "={{JSON.stringify($json)}}"
      }
    },
    {
      "name": "Process Results",
      "type": "n8n-nodes-base.function",
      "parameters": {
        "functionCode": "// Process analysis results and add to tables"
      }
    }
  ]
}
```

## Running the API

### **Start the API Server:**
```bash
cd /Users/ryanburt/pain_based_predictive_outreach_agent
python3 src/api/reactive_analyzer_api.py
```

### **Test the API:**
```bash
# Health check
curl http://localhost:8001/health

# Single company analysis
curl -X POST http://localhost:8001/analyze-company \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test Company",
    "domain": "testcompany.com",
    "industry": "Technology"
  }'
```

## Performance Considerations

### **Batch Processing:**
- Use batch endpoint for multiple companies
- Background processing for large batches
- Rate limiting to prevent API overload

### **Caching:**
- Cache analysis results for 24 hours
- Skip re-analysis of recently analyzed companies
- Store results in Clay for quick access

### **Monitoring:**
- Log all analysis requests
- Track analysis performance
- Monitor signal quality and accuracy

## Next Steps

1. **Deploy API**: Set up the reactive analyzer API
2. **Clay Integration**: Create HTTP request nodes in Clay
3. **n8n Workflow**: Build the complete workflow
4. **Testing**: Test with sample company data
5. **Production**: Deploy and monitor performance

This system provides a complete reactive analysis solution that integrates seamlessly with your existing Clay and n8n infrastructure.
