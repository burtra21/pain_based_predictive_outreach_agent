# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Clay Configuration
    CLAY_API_KEY = os.getenv('CLAY_API_KEY')
    CLAY_WORKSPACE = os.getenv('CLAY_WORKSPACE')
    CLAY_WEBHOOK_URL = os.getenv('CLAY_WEBHOOK_URL')
    CLAY_WEBHOOK_SECRET = os.getenv('CLAY_WEBHOOK_SECRET')
    
    # n8n Configuration
    N8N_URL = os.getenv('N8N_URL', 'http://localhost:5678')
    N8N_API_KEY = os.getenv('N8N_API_KEY')
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/bta')
    
    # Redis (for queuing)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # REMOVED: DarkOwl
    # DARKOWL_API_KEY = os.getenv('DARKOWL_API_KEY')  # REMOVED
    
    # Optional low-cost APIs
    HIBP_API_KEY = os.getenv('HIBP_API_KEY')  # $3.50/month - optional
    SHODAN_API_KEY = os.getenv('SHODAN_API_KEY')  # $59/month - optional
    SERPAPI_API_KEY = os.getenv('SERPAPI_API_KEY')  # For enhanced search capabilities
    
    # Still needed
    WAPPALYZER_API_KEY = os.getenv('WAPPALYZER_API_KEY')
    
    # Scoring Thresholds
    MIN_PAIN_SCORE = 70  # Minimum score to qualify for outreach
    POST_BREACH_THRESHOLD = 90
    SKILLS_GAP_THRESHOLD = 75
    INSURANCE_THRESHOLD = 80
    
    # Rate Limits
    CLAY_RATE_LIMIT = 100  # requests per minute
    OUTREACH_DAILY_LIMIT = 500
    
    # Timing
    BUSINESS_HOURS_START = 9  # 9 AM
    BUSINESS_HOURS_END = 17  # 5 PM
    TIMEZONE = 'America/Chicago'

config = Config()