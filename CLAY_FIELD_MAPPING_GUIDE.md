# Clay Field Mapping Guide - Exact Setup Instructions

## 🎯 **Your Clay Field Mapping Setup**

Based on your field mapping structure, here's the **exact Clay HTTP Request configuration**:

---

## 📋 **Clay HTTP Request Node Configuration**

### **Step 1: Basic Setup**

**URL**: `http://localhost:8002/analyze-enriched-company`
**Method**: `POST`
**Headers**:
```json
{
  "Content-Type": "application/json"
}
```

### **Step 2: Request Body** (Your Mapped Fields)

```json
{
  "company_name": "{{company_name}}",
  "domain": "{{domain}}",
  "industry": "{{industry}}",
  "employeeCount": {{employee_count}},
  "foundedOn": {{year}},
  "description": "{{description}}",
  "headquarter": "{{hq_location}}",
  "specialities": {{specialities}},
  "linkedinUrl": "{{url}}"
}
```

### **Step 3: Clay Field Variables Required**

Make sure your Clay table has these **exact field names**:
- ✅ `company_name`
- ✅ `domain` 
- ✅ `industry`
- ✅ `employee_count`
- ✅ `year`
- ✅ `description`
- ✅ `hq_location`
- ✅ `specialities`
- ✅ `url`

---

## 🔧 **Clay Table Structure Recommendations**

### **Recommended Clay Table Schema**:
```yaml
Table: companies_enriched
Fields:
  - company_name: Text
  - domain: URL
  - industry: Text
  - employee_count: Number
  - year: Number (founded year)
  - description: Large text
  - hq_location: Text (city, state format)
  - specialities: List
  - linkedin_url: URL (map to 'url' field)
  - website_url: URL
  - employee_range: Text
  
Enriched Fields (add these for better analysis):
  - priority_score: Number
  - signal_count: Number
  - last_analyzed: Date
  - analysis_status: Text
```

---

## 🚀 **Complete Clay Workflow Steps**

### **Step 1: HTTP Request Node**
```json
{
  "method": "POST",
  "url": "http://localhost:8002/analyze-enriched-company",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "company_name": "{{company_name}}",
    "domain": "{{domain}}",
    "industry": "{{industry}}",
    "employeeCount": {{employee_count}},
    "foundedOn": {{year}},
    "description": "{{description}}",
    "headquarter": "{{hq_location}}",
    "specialities": {{specialities}},
    "linkedinUrl": "{{url}}"
  }
}
```

### **Step 2: Response Handler Function**
```javascript
// Parse the Python API response
const response = $input.first().json;

if (!response.success) {
  throw new Error(`Analysis failed: ${response.message}`);
}

// Extract the analysis results
const result = {
  company_name: response.company_name,
  domain: response.domain,
  priority_score: response.priority_score,
  signals_found: response.signals_found,
  signals: response.signals,
  data_richness: response.data_richness,
  analysis_time: response.analysis_time,
  analysis_timestamp: new Date().toISOString()
};

// Filter for high-priority signals (optional)
const highPrioritySignals = result.signals.filter(signal => 
  signal.signal_strength >= 0.8
);

return [{
  json: {
    ...result,
    high_priority_signals: highPrioritySignals.length,
    campaign_ready: result.signals_found > 0
  }
}];
```

### **Step 3: Store Results**
Add a **"Add Row"** or **"Update Row"** node:
- **Table**: `pain_signals` or `analyzed_companies`
- **Fields**: Map the response data to your Clay tables

### **Step 4: Campaign Generation** (Optional)
```javascript
// Generate campaigns for companies with signals
const analysis = $input.first().json;

if (!analysis.campaign_ready) {
  return [{ json: { skip_campaign: true, reason: "No signals found" } }];
}

const campaigns = analysis.signals.map(signal => ({
  company_name: analysis.company_name,
  domain: analysis.domain,
  signal_type: signal.signal_type,
  signal_strength: signal.signal_strength,
  
  // Email campaign
  email_subject: generateSubject(signal.signal_type, analysis.company_name),
  email_body: generateEmailBody(signal, analysis.company_name),
  
  // LinkedIn campaign  
  linkedin_message: generateLinkedInMessage(signal, analysis.company_name),
  
  // Metadata
  priority: signal.signal_strength >= 0.9 ? 'urgent' : 'high',
  create d_at: new Date().toISOString(),
  status: 'ready_for_outreach'
}));

return campaigns.map(campaign => ({ json: campaign }));
```

---

## 📊 **Expected Response Format**

### **Success Response**:
```json
{
  "success": true,
  "company_name": "Path Robotics",
  "domain": "path-robotics.com",
  "priority_score": 0.95,
  "signals_found": 3,
  "signals": [
    {
      "signal_type": "breach_mention_detected",
      "signal_strength": 0.9,
      "signal_date": "2025-09-29T12:30:00Z",
      "raw_data": {
        "detection_method": "serpapi_news_search",
        "confidence": "very_high",
        "news_title": "...",
        "news_url": "..."
      },
      "source": "company_analysis_serpapi"
    }
  ],
  "analysis_time": 25.5,
  "data_richness": "rich"
}
```

### **Error Response** (if analysis fails):
```json
{
  "detail": [
    {
      "type": "validation_error",
      "loc": ["body", "employeeCount"],
      "msg": "field required"
    }
  ]
}
```

---

## 🔥 **Testing Your Clay Setup**

### **Test Sample Data** (add this row to test):
```yaml
company_name: "Test Robotics Corp"
domain: "test-robotics.com"
industry: "Industrial Automation"
employee_count: 150
year: 2020
description: "Automated manufacturing solutions for automotive industry"
hq_location: "Detroit, MI"
specialities: ["Robotics", "Manufacturing", "AI"]
linkedin_url: "https://linkedin.com/company/test-robotics"
```

### **Expected Analysis Results**:
- **Priority Score**: 0.9+ (high data richness)
- **Signals**: 2-3 pain signals expected
- **Analysis Time**: 20-30 seconds
- **Campaign Ready**: ✅ Yes

---

## 🚨 **Common Clay Setup Issues & Solutions**

### **Issue 1: Field Mapping Errors**
**Problem**: `{{company_name}}` returns empty
**Solution**: 
- Check exact field names in Clay table
- Ensure field contains data (not null/empty)
- Use Clay's "Preview" to verify field values

### **Issue 2: JSON Parsing Errors**
**Problem**: Malformed JSON in request body
**Solution**:
- Use Clay's JSON validator
- Test with static values first
- Check for quotes around variables: `"{{field}}"` vs `{{field}}`

### **Issue 3: Empty Response**
**Problem**: No signals generated
**Solution**:
- Verify API endpoint: `http://localhost:8002/analyze-enriched-company`
- Check company has valid `domain` field
- Ensure API server is running (port 8002)

### **Issue 4: Type Mismatches**
**Problem**: `employeeCount` expects number, gets string
**Solution**:
- Clay field output: `{{employee_count|number}}`
- Or handle conversion in Function node

---

## 💡 **Advanced Field Mapping Tips**

### **1. Conditional Fields**
```javascript
// Only send years > 1990
"foundedOn": {{year >= 1990 ? year : null}}
```

### **2. Array Handling**
```javascript
// Convert specialities list to comma-separated string
"specialities": "{{specialities|join(', ')}}"
```

### **3. Number Validation**
```javascript
// Ensure employee count is valid number
"employeeCount": {{employee_count > 0 ? employee_count : 0}}
```

### **4. URL Validation**
```javascript
// Add protocol if missing
"domain": "{{domain|prepend('https://')|removePrefixIfContains('https://')}}"
```

---

## 🔗 **Clay HTTP Request Test Configuration**

### **Production-Ready Clay Node Setup**:

**Node**: HTTP Request
**Method**: POST
**URL**: `http://your-server.com:8002/analyze-enriched-company`
**Headers**: 
```json
{
  "Content-Type": "application/json",
  "User-Agent": "Clay-PainAnalyzer/1.0"
}
```
**Body**:
```json
{
  "company_name": "{{company_name}}",
  "domain": "{{domain}}",
  "industry": "{{industry}}",
  "employeeCount": {{employee_count}},
  "foundedOn": {{year}},
  "description": "{{description}}",
  "headquarter": "{{hq_location}}",
  "specialities": {{specialities}},
  "linkedinUrl": "{{linkedin_url}}"
}
```
**Options**:
- **Timeout**: 60 seconds
- **Retry**: 3 attempts
- **Error Handling**: Continue on error

---

## ✅ **Ready to Test!**

Your field mapping setup is perfect for Clay integration. The API on **port 8002** will:

1. ✅ **Accept your mapped fields**
2. ✅ **Calculate priority scores** 
3. ✅ **Generate pain signals** via SERPAPI/HIBP
4. ✅ **Return structured data** for Clay workflows
5. ✅ **Enable campaign generation** based on signals

**Start with a single test row, then scale to your full Clay database!**
