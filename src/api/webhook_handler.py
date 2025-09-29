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