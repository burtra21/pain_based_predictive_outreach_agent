# Clay HTTP Request Setup Guide - Complete Instructions

## 🎯 Overview

This guide shows you how to set up **HTTP Request nodes in Clay** to send your enriched company data to our Python pain analysis API and get automated campaigns back.

---

## 📋 Clay HTTP Request Node Configuration

### **Step 1: HTTP Request Node Setup**

**Node Type**: `n8n-nodes-base.httpRequest`

**Configuration**:
```json
{
  "method": "POST",
  "url": "http://localhost:8002/analyze-enriched-batch",
  "authentication": "none",
  "headers": {
    "Content-Type": "application/json"
  },
  "jsonParameters": true,
  "timeout": 120000,
  "retry": {
    "enabled": true, 
    "maxRetries": 3
  }
}
```

### **Step 2: Request Body Payload**

**Body Parameters** (JSON):
```json
{
  "companies": [
    {
      "company_name": "Path Robotics",
      "companyId": 9261371,
      "websiteUrl": "https://www.path-robotics.com", 
      "industry": "Industrial Automation",
      "universalName": "path-robotics",
      "employeeCount": 164,
      "employeeCountRange": {
        "end": 200,
        "start": 51
      },
      "foundedOn": {
        "year": 2014
      },
      "description": "Path Robotics was founded by brothers Andy and Alex Lonsberry with a desire to help fill workforce gaps in the manufacturing industry.",
      "tagline": "We're enabling robots to build, so humans can create.",
      "locations": [
        {
          "city": "Columbus",
          "line1": "3950 Business Park Dr",
          "country": "US", 
          "postalCode": "43204",
          "headquarter": true,
          "geographicArea": "Ohio"
        }
      ],
      "headquarter": {
        "city": "Columbus",
        "line1": "3950 Business Park Dr", 
        "country": "US",
        "postalCode": "43204", 
        "geographicArea": "Ohio"
      },
      "specialities": [
        "Fluid and Solid Mechanics",
        "Robotics and Automation", 
        "Software and Database Solutions",
        "manufacturing",
        "welding",
        "automation",
        "artificial intelligence"
      ],
      "followerCount": 41914,
      "linkedinUrl": "https://www.linkedin.com/company/path-robotics/",
      "needs_pain_analysis": true,
      "priority_score": null
    }
  ],
  "include_tech_analysis": true,
  "include_contact_enrichment": false, 
  "priority_filter": 0.7,
  "analysis_options": {
    "signal_types": [
      "breach_history_check",
      "tech_stack_analysis", 
      "hibp_breach_check",
      "github_exposure_check",
      "job_posting_analysis"
    ],
    "priority_score_threshold": 0.7,
    "generate_campaigns": true,
    "batch_size": 10
  }
}
```

---

## 🔧 Environment Variables Needed in Clay

### **Clay Environment Variables**:
```yaml
# API Configuration
CLAY_BASE_URL: https://api.clay.com
CLAY_API_KEY: your_clay_api_key_here
CLAY_WEBHOOK_URL: your_existing_clay_webhook_url
CLAY_WEBHOOK_SECRET: your_webhook_secret

# Python API Endpoint  
PYTHON_API_URL: http://localhost:8002
ENHANCED_API_PORT: 8002

# External APIs
SERPAPI_API_KEY: cee7bd10d527454d6884388273cc22762ffb86cc4eee611a5e08881310756a30
HIBP_API_KEY: your_hibp_api_key_here
```

---

## 📡 Expected Response Format

### **Success Response**:
```json
{
  "success": true,
  "message": "Processed 1 enriched companies",
  "summary": {
    "original_count": 1,
    "filtered_count": 1, 
    "processed_count": 1,
    "total_signals": 3,
    "processing_time": 28.5,
    "priority_threshold": 0.7
  },
  "results": [
    {
      "company_name": "Path Robotics",
      "domain": "path-robotics.com",
      "signals": [
        {
          "company_name": "Path Robotics" 
          "domain": "path-robotics.com",
          "signal_type": "breach_mention_detected",
          "signal_date": "2025-09-29T12:30:00Z",
          "signal_strength": 0.9,
          "raw_data": {
            "search_query": "\"Path Robotics\" data breach 2024",
            "detection_method": "serpapi_news_search",
            "confidence": "very_high",
            "news_title": "Industrial Robots Vulnerable to Cyber Attacks",
            "news_url": "https://example.com/industrial-security",
            "news_date": "Dec 15, 2024"
          },
          "source": "company_analysis_serpapi"
        },
        {
          "company_name": "Path Robotics",
          "domain": "path-robotics.com", 
          "signal_type": "critical_security_gaps",
          "signal_date": "2025-09-29T12:30:15Z",
          "signal_strength": 0.85,
          "raw_data": {
            "missing_tools": ["EDR", "SIEM_LOG", "MDR", "BACKUP"],
            "risk_level": "CRITICAL",
            "dwell_time": "EXTREME",
            "detection_method": "builtwith_analysis"
          },
          "source": "enhanced_tech_analysis"
        },
        {
          "company_name": "Path Robotics",
          "domain": "path-robotics.com",
          "signal_type": "ransomware_vulnerability_detected", 
          "signal_date": "2025-09-29T12:30:30Z",
          "signal_strength": 0.95,
          "raw_data": {
            "vulnerability_confirmed": true,
            "missing_protections": ["EDR", "MDR", "BACKUP"],
            "outreach_message": "dwell_time_alert",
            "detection_method": "builtwith_vulnerability_scan"
          },
          "source": "enhanced_tech_analysis"
        }
      ],
      "priority_score": 0.95,
      "data_richness": "rich"
    }
  ]
}
```

---

## 🚀 Step-by-Step Clay Setup Instructions

### **1. Create HTTP Request Node**

In Clay workflows:
1. **Drag HTTP Request node** into your workflow
2. **Set Method** to `POST`
3. **Set URL** to `http://localhost:8002/analyze-enriched-batch`
4. **Add Headers**:
   ```
   Content-Type: application/json
   ```

### **2. Configure Request Body**

In the **Body Parameters** section:
1. **Switch to JSON mode**
2. **Paste the payload** from Step 2 above
3. **Use variables** like `{{company_name}}`, `{{websiteUrl}}` to inject your Clay data

### **3. Set Response Handling**

Add **Function node** after HTTP Request:
```javascript
// Parse response and extract high-priority signals
const response = $input.first().json;

if (!response.success) {
  throw new Error(`Analysis failed: ${response.message}`);
}

// Get companies with signals
const companiesWithSignals = response.results.filter(
  result => result.signals.length > 0
);

// Format for Clay tables
const enrichedData = companiesWithSignals.map(result => ({
  company_name: result.company_name,
  domain: result.domain,
  signals_count: result.signals.length,
  priority_score: result.priority_score,
  highest_signal_strength: Math.max(...result.signals.map(s => s.signal_strength)),
  signals: result.signals,
  analysis_timestamp: new Date().toISOString(),
  ready_for_campaign: true
}));

return enrichedData.map(item => ({ json: item }));
```

### **4. Store Results in Clay Tables**

Add **Add Row** node:
- **Table**: `pain_signals` or `analyzed_companies`
- **Use data** from Function node output

### **5. Generate Campaigns** (Optional)

Add **Campaign Generator** node:
```javascript
// Generate campaigns based on signals
const items = $input.all();
const campaigns = [];

items.forEach(item => {
  const signals = item.json.signals;
  
  signals.forEach(signal => {
    const campaign = {
      company_name: item.json.company_name,
      domain: item.json.domain,
      signal_type: signal.signal_type,
      signal_strength: signal.signal_strength,
      
      email_subject: generateEmailSubject(signal, item.json.company_name),
      email_body: generateEmailBody(signal, item.json.company_name, item.json.domain),
      
      linkedin_message: generateLinkedInMessage(signal, item.json.company_name),
      
      priority: signal.signal_strength > 0.9 ? 'urgent' : 'high',
      scheduled_send_time: new Date(Date.now() + (4 * 60 * 60 * 1000)).toISOString(), // 4 hours from now
      
      status: 'ready_for_review',
      created_at: new Date().toISOString()
    };
    
    campaigns.push(campaign);
  });
});

return campaigns.map(campaign => ({ json: campaign }));

// Helper functions
function generateEmailSubject(signal, companyName) {
  const subjects = {
    'breach_mention_detected': `Security Response Required - ${companyName}`,
    'critical_security_gaps': `Urgent: Critical Security Gaps Detected`, 
    'ransomware_vulnerability': `CRITICAL: Ransomware Protection Needed`,
    'tech_gap_analysis': `Technology Security Assessment - ${companyName}`
  };
  return subjects[signal.signal_type] || `Cybersecurity Support - ${companyName}`;
}

function generateEmailBody(signal, companyName, domain) {
  const baseIntro = `Hi there,\n\nWe've identified cybersecurity vulnerabilities affecting ${companyName}.\n\n`;
  
  const signalDetails = {
    'breach_mention_detected': `Our monitoring detected ${companyName} mentioned in recent security incident reports. We specialize in rapid incident response and recovery.\n\nWe can provide:\n• Immediate incident response support\n• Forensic analysis and containment\n• Recovery planning and implementation\n• Prevention strategies for future incidents`,
    
    'critical_security_gaps': `${companyName} shows critical security gaps that require immediate attention:\n\n${signal.raw_data.missing_tools ? '• Missing: ' + signal.raw_data.missing_tools.join(', ') : ''}\n• Risk Level: ${signal.raw_data.risk_level || 'HIGH'}\n• Detection Time: ${signal.raw_data.dwell_time || '277 days'}\n\nWe specialize in rapid security implementations for companies your size.`,
    
    'ransomware_vulnerability': `${companyName} appears vulnerable to ransomware attacks based on current security configurations.\n\nMissing protections detected:\n${signal.raw_data.missing_protections ? '• ' + signal.raw_data.missing_protections.join('\n• ') : ''}\n\nPriority response available. Let's discuss immediate protection strategies.`
  };
  
  const closing = `\n\nWould you be interested in a free consultation to discuss strengthening your security posture?\n\nBest regards,\nBlueTeam Alpha`;
  
  return baseIntro + (signalDetails[signal.signal_type] || 'We identified security gaps that need immediate attention.') + closing;
}

function generateLinkedInMessage(signal, companyName) {
  return `Security alert: ${companyName} has urgent cybersecurity gaps that need immediate attention. We specialize in rapid security implementations for your industry. Happy to connect and discuss how we can help protect your business.`;
}
```

---

## 🔥 Advanced Clay Integration Features

### **1. Conditional Processing**

Only send companies that meet criteria:
```javascript
// Filter companies before sending to Python API
const qualifiedCompanies = items.filter(item => {
  const company = item.json;
  
  return company.employeeCount >= 50 && // Minimum size
         company.company_name &&        // Has name
         company.websiteUrl &&          // Has website
         !company.has_been_analyzed;    // Not already analyzed
});

if (qualifiedCompanies.length === 0) {
  return [{ json: { message: "No qualified companies found", skip_analysis: true } }];
}

return qualifiedCompanies.map(company => ({ json: company }));
```

### **2. Batch Processing Optimization**

Send companies in batches of 10:
```javascript
// Split into batches of 10 companies
const companies = $input.all();
const batchSize = 10;
const batches = [];

for (let i = 0; i < companies.length; i += batchSize) {
  batches.push(companies.slice(i, i + batchSize));
}

console.log(`Processing ${batches.length} batches`);

return batches.map((batch, index) => ({
  json: {
    batch_number: index + 1,
    total_batches: batches.length,
    companies: batch.map(item => item.json)
  }
}));
```

### **3. Error Handling**

Robust error handling:
```javascript
// Error handling and retry logic
const tryAnalysis = async (companyData) => {
  const maxRetries = 3;
  let attempt = 0;
  
  while (attempt < maxRetries) {
    try {
      // Make HTTP request to Python API
      const response = await fetch('http://localhost:8002/analyze-enriched-batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ companies: [companyData] })
      });
      
      if (response.ok) {
        return await response.json();
      }
      
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      
    } catch (error) {
      attempt++;
      console.error(`Attempt ${attempt} failed for ${companyData.company_name}:`, error);
      
      if (attempt >= maxRetries) {
        return {
          success: false,
          error: error.message,
          company: companyData.company_name
        };
      }
      
      // Wait before retry (exponential backoff)
      await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
    }
  }
};
```

---

## 📊 Monitoring & Success Metrics

### **Track These Metrics**:
- **Analysis Success Rate**: Successful API calls / Total attempts
- **Signal Generation Rate**: Signals found / Companies analyzed  
- **Campaign Creation Rate**: Campaigns created / Signals found
- **Response Time**: Average API response time
- **Error Rate**: Failed requests / Total requests

### **Success Indicators**:
✅ **API Response Time**: < 30 seconds per company  
✅ **Signal Generation**: 2-5 signals per company average  
✅ **Priority Score**: > 0.7 for actionable signals  
✅ **Error Rate**: < 5% failed requests  
✅ **Clay Integration**: Successful webhook delivery  

---

## 🚀 Ready to Deploy?

**Your Clay HTTP setup should:**

1. ✅ **Send enriched company data** to Python API (port 8002)
2. ✅ **Process pain signals** automatically  
3. ✅ **Store results** in Clay tables
4. ✅ **Generate campaigns** based on signals
5. ✅ **Handle errors** gracefully with retry logic

**Test with Path Robotics sample data first, then scale to full batches!**

This setup gives you **automated pain-based outreach** from Clay → Python → Clay in minutes!
