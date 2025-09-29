#!/usr/bin/env python3
"""
Scheduled Breach Collector Runner
Automatically runs breach collection on Monday and Wednesday mornings
"""

import sys
import os
import schedule
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.dirname(__file__))

from clay_client import ClayClient
from collectors.breach_collector import BreachCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/scheduled_breach_runner.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

class ScheduledBreachRunner:
    """Scheduled runner for breach collection with duplicate detection"""
    
    def __init__(self):
        self.setup_logging_dir()
        self.clay_client = None
        self.breach_collector = None
        self._initialize_components()
    
    def setup_logging_dir(self):
        """Ensure logs directory exists"""
        logs_dir = 'logs'
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
    
    def _initialize_components(self):
        """Initialize Clay client and breach collector"""
        try:
            # Get credentials from environment
            api_key = os.getenv('CLAY_API_KEY')
            workspace = os.getenv('CLAY_WORKSPACE')
            webhook_url = os.getenv('CLAY_WEBHOOK_URL')
            
            if not webhook_url:
                logger.error("CLAY_WEBHOOK_URL not configured in environment")
                return False
            
            # Initialize Clay client
            self.clay_client = ClayClient(api_key, workspace)
            
            # Initialize breach collector
            self.breach_collector = BreachCollector(self.clay_client)
            
            logger.info("Successfully initialized breach collector components")
            logger.info(f"Clay webhook configured: {webhook_url[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            return False
    
    def run_scheduled_collection(self):
        """Run breach collection with full logging"""
        run_start = datetime.now()
        logger.info("="*60)
        logger.info(f"Starting scheduled breach collection at {run_start}")
        
        try:
            if not self.breach_collector:
                logger.error("Breach collector not initialized")
                return
            
            # Run the collection
            self.breach_collector.run_collection()
            
            run_duration = (datetime.now() - run_start).total_seconds()
            logger.info(f"Scheduled breach collection completed in {run_duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Error in scheduled breach collection: {e}", exc_info=True)
        finally:
            logger.info("="*60)
    
    def start_scheduler(self):
        """Start the scheduler with Monday and Wednesday morning runs"""
        if not self._initialize_components():
            logger.error("Failed to initialize - exiting")
            return
        
        # Schedule for Monday and Wednesday at 7:00 AM (Chicago time)
        schedule.every().monday.at("07:00").do(self.run_scheduled_collection)
        schedule.every().wednesday.at("07:00").do(self.run_scheduled_collection)
        
        logger.info("Scheduled breach collector started with the following schedule:")
        logger.info("- Mondays at 7:00 AM (Chicago Time)")
        logger.info("- Wednesdays at 7:00 AM (Chicago Time)")
        logger.info("- Automatic duplicate detection (only new data sent)")
        logger.info("- Batched webhook delivery to Clay")
        
        # Show next scheduled runs
        jobs = schedule.jobs
        if jobs:
            logger.info("\nNext scheduled runs:")
            for job in jobs:
                logger.info(f"- {job.next_run}")
        
        logger.info("Scheduler running... Press Ctrl+C to stop")
        
        # Main scheduler loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {e}", exc_info=True)

def main():
    """Main entry point"""
    print("🚀 BTA Breach Collector - Automated Scheduler")
    print("Runs Monday & Wednesday mornings with duplicate detection")
    print()
    
    runner = ScheduledBreachRunner()
    runner.start_scheduler()

if __name__ == "__main__":
    main()
