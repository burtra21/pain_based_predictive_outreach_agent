"""
BTA Orchestrator - Improved Version
Enhanced with better error handling, separation of concerns, and maintainability
"""

import json
import signal
import sys
import schedule
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
import logging
from logging.handlers import RotatingFileHandler
import threading
from dataclasses import dataclass
from enum import Enum

# Import our modules
from config.settings import config
from clay_client import ClayClient
from collectors.breach_collector import BreachCollector
from collectors.job_collector import JobPostingCollector
from collectors.free_darkweb_monitor import FreeThreatsMonitor
from collectors.insurance_intel import InsuranceIntelCollector
from collectors.company_analyzer import CompanyAnalyzer
from scoring.edp_scorer import EDPScorer
from campaigns.campaign_generator import CampaignGenerator


class SignalType(Enum):
    """Enum for signal types"""
    ACTIVE_RANSOMWARE = "active_ransomware"
    BREACH_NOTIFICATION = "breach_notification"
    JOB_POSTING = "job_posting"


@dataclass
class CampaignResult:
    """Data class for campaign generation results"""
    campaigns_created: int
    prospects_processed: int
    errors: List[str]


class LoggerSetup:
    """Centralized logging configuration"""
    
    @staticmethod
    def configure_logging() -> logging.Logger:
        """Configure enhanced logging with file rotation"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(detailed_formatter)
        logger.addHandler(console_handler)
        
        # File handler with rotation
        try:
            file_handler = RotatingFileHandler(
                'logs/bta_orchestrator.log',
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(detailed_formatter)
            logger.addHandler(file_handler)
        except (OSError, IOError) as e:
            logger.warning(f"Could not create log file handler: {e}")
        
        return logger


class ConfigValidator:
    """Validates configuration settings"""
    
    @staticmethod
    def validate_config() -> None:
        """Validate required configuration values"""
        required_attrs = [
            'CLAY_API_KEY', 
            'CLAY_WORKSPACE', 
            'OUTREACH_DAILY_LIMIT', 
            'MIN_PAIN_SCORE'
        ]
        
        missing_config = []
        for attr in required_attrs:
            if not hasattr(config, attr) or getattr(config, attr) is None:
                missing_config.append(attr)
        
        if missing_config:
            raise ValueError(f"Missing required configuration: {missing_config}")


class BTAOrchestrator:
    """
    Main orchestrator for BTA (Business Threat Analysis) operations
    Handles data collection, scoring, and campaign generation
    """
    
    # Constants
    COLLECTION_RETRY_ATTEMPTS = 3
    SCORING_BATCH_SIZE = 50
    SCHEDULER_CHECK_INTERVAL = 60  # seconds
    
    def __init__(self):
        """Initialize the orchestrator with all required components"""
        # Validate configuration first
        ConfigValidator.validate_config()
        
        # Set up logging
        self.logger = LoggerSetup.configure_logging()
        
        # Initialize shutdown flag
        self._shutdown_requested = threading.Event()
        
        # Initialize Clay client with error handling
        try:
            self.clay_client = ClayClient(
                config.CLAY_API_KEY,
                config.CLAY_WORKSPACE
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize Clay client: {e}")
            raise
        
        # Initialize collectors
        self._initialize_collectors()
        
        # Initialize processors
        self._initialize_processors()
        
        # State management
        self.daily_limit_remaining = config.OUTREACH_DAILY_LIMIT
        self.stats = {
            'cycles_completed': 0,
            'total_campaigns_created': 0,
            'total_errors': 0
        }
        
        # Register signal handlers for graceful shutdown
        self._register_signal_handlers()
        
        self.logger.info("BTAOrchestrator initialized successfully")
    
    def _initialize_collectors(self) -> None:
        """Initialize all data collectors with error handling"""
        try:
            # Proactive collectors (find new data)
            self.breach_collector = BreachCollector(self.clay_client)
            self.job_collector = JobPostingCollector(self.clay_client)
            self.threats_monitor = FreeThreatsMonitor(self.clay_client)
            self.insurance_intel = InsuranceIntelCollector(self.clay_client)
            
            # Reactive analyzer (analyze existing companies)
            self.company_analyzer = CompanyAnalyzer(self.clay_client)
            
            self.logger.info("All collectors initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize collectors: {e}")
            raise
    
    def _initialize_processors(self) -> None:
        """Initialize scoring and campaign generation components"""
        try:
            self.scorer = EDPScorer(self.clay_client)
            self.campaign_gen = CampaignGenerator(self.clay_client)
            self.logger.info("All processors initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize processors: {e}")
            raise
    
    def _register_signal_handlers(self) -> None:
        """Register signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating shutdown...")
            self.request_shutdown()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def request_shutdown(self) -> None:
        """Request graceful shutdown"""
        self.logger.info("Shutdown requested")
        self._shutdown_requested.set()
    
    @contextmanager
    def _error_context(self, operation_name: str):
        """Context manager for consistent error handling"""
        start_time = datetime.now()
        try:
            self.logger.info(f"Starting {operation_name}")
            yield
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Completed {operation_name} in {duration:.2f}s")
        except Exception as e:
            self.stats['total_errors'] += 1
            self.logger.error(f"Error in {operation_name}: {e}", exc_info=True)
            raise
    
    def _collect_breach_data(self) -> bool:
        """Collect breach data with error handling"""
        try:
            self.breach_collector.run_collection()
            return True
        except Exception as e:
            self.logger.error(f"Breach collection failed: {e}")
            return False
    
    def _collect_job_data(self) -> bool:
        """Collect job posting data with error handling"""
        try:
            self.job_collector.run_collection()
            return True
        except Exception as e:
            self.logger.error(f"Job collection failed: {e}")
            return False
    
    def _collect_threat_data(self) -> bool:
        """Collect threat intelligence data with error handling"""
        try:
            self.threats_monitor.run_collection()
            return True
        except Exception as e:
            self.logger.error(f"Threat collection failed: {e}")
            return False
    
    def _collect_insurance_data(self) -> bool:
        """Collect insurance intelligence data with error handling"""
        try:
            self.insurance_intel.run_collection()
            return True
        except Exception as e:
            self.logger.error(f"Insurance collection failed: {e}")
            return False
    
    def _analyze_existing_companies(self) -> bool:
        """Analyze existing companies for pain signals with error handling"""
        try:
            self.company_analyzer.run_analysis(batch_size=100)
            return True
        except Exception as e:
            self.logger.error(f"Company analysis failed: {e}")
            return False
    
    def run_daily_collection(self) -> Dict[str, bool]:
        """
        Run all data collectors with individual error handling
        Returns: Dictionary of collection results
        """
        with self._error_context("daily data collection"):
            results = {
                'breach_data': self._collect_breach_data(),
                'job_data': self._collect_job_data(),
                'threat_data': self._collect_threat_data(),
                'insurance_data': self._collect_insurance_data(),
                'company_analysis': self._analyze_existing_companies()
            }
            
            successful_collections = sum(results.values())
            self.logger.info(
                f"Collection results: {successful_collections}/{len(results)} successful"
            )
            
            return results
    
    def _get_unscored_companies(self) -> List[Dict]:
        """Get unscored companies from the database"""
        try:
            return self.clay_client.query_table(
                'company_universe',
                {'scored': False}
            )
        except Exception as e:
            self.logger.error(f"Failed to get unscored companies: {e}")
            return []
    
    def _process_ransomware_signals(self, company: Dict, signals: List[Dict]) -> Optional[Dict]:
        """Process ransomware signals for a company"""
        ransomware_signals = [
            s for s in signals 
            if s.get('signal_type') == SignalType.ACTIVE_RANSOMWARE.value
        ]
        
        if not ransomware_signals:
            return None
        
        self.logger.warning(f"RANSOMWARE VICTIM DETECTED: {company['domain']}")
        
        return {
            'pain_score': 100,  # Maximum urgency
            'primary_edp': SignalType.ACTIVE_RANSOMWARE.value,
            'segment': 'post_breach_survivor',
            'domain': company['domain']
        }
    
    def _score_single_company(self, company: Dict) -> Optional[Dict]:
        """Score a single company with error handling"""
        try:
            # Calculate base score
            score_data = self.scorer.calculate_company_score(company['domain'])
            
            # Check for special high-priority signals
            signals = self.clay_client.query_table(
                'pain_signals',
                {'domain': company['domain']}
            )
            
            # Handle ransomware victims specially
            ransomware_override = self._process_ransomware_signals(company, signals)
            if ransomware_override:
                score_data.update(ransomware_override)
            
            # Only keep if above threshold
            if score_data['pain_score'] >= config.MIN_PAIN_SCORE:
                # Update database records
                self.clay_client.add_row('scored_prospects', score_data)
                self.clay_client.add_row('company_universe', {
                    'domain': company['domain'],
                    'scored': True
                })
                return score_data
            
            # Mark as scored even if below threshold
            self.clay_client.add_row('company_universe', {
                'domain': company['domain'],
                'scored': True
            })
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error scoring company {company.get('domain', 'unknown')}: {e}")
            return None
    
    def score_new_companies(self) -> List[Dict]:
        """Score all unscored companies with batch processing"""
        with self._error_context("company scoring"):
            unscored = self._get_unscored_companies()
            self.logger.info(f"Found {len(unscored)} companies to score")
            
            if not unscored:
                return []
            
            qualified_prospects = []
            
            # Process in batches to avoid memory issues
            for i in range(0, len(unscored), self.SCORING_BATCH_SIZE):
                batch = unscored[i:i + self.SCORING_BATCH_SIZE]
                self.logger.info(f"Processing scoring batch {i//self.SCORING_BATCH_SIZE + 1}")
                
                for company in batch:
                    if self._shutdown_requested.is_set():
                        self.logger.info("Shutdown requested during scoring")
                        break
                    
                    scored_prospect = self._score_single_company(company)
                    if scored_prospect:
                        qualified_prospects.append(scored_prospect)
                
                if self._shutdown_requested.is_set():
                    break
            
            self.logger.info(f"Scored {len(qualified_prospects)} qualified prospects")
            return qualified_prospects
    
    def _get_company_info(self, domain: str) -> Optional[Dict]:
        """Get company information for a domain"""
        try:
            companies = self.clay_client.query_table(
                'company_universe',
                {'domain': domain}
            )
            return companies[0] if companies else None
        except Exception as e:
            self.logger.error(f"Error getting company info for {domain}: {e}")
            return None
    
    def _process_ransomware_campaign(self, prospect: Dict) -> None:
        """Process special ransomware victim campaign data"""
        try:
            signals = self.clay_client.query_table(
                'pain_signals',
                {
                    'domain': prospect['domain'], 
                    'signal_type': SignalType.ACTIVE_RANSOMWARE.value
                }
            )
            
            if signals and signals[0].get('raw_data'):
                raw_data = json.loads(signals[0]['raw_data'])
                prospect['ransomware_group'] = raw_data.get('ransomware_group', 'Unknown')
                prospect['hours_since_posting'] = raw_data.get('hours_since_posting', 0)
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Error processing ransomware data: {e}")
    
    def generate_campaigns(self, prospects: List[Dict]) -> CampaignResult:
        """Generate campaigns for qualified prospects with comprehensive validation and error handling"""
        with self._error_context("campaign generation"):
            result = CampaignResult(
                campaigns_created=0,
                prospects_processed=0,
                errors=[]
            )
            
            # Input validation
            if not prospects:
                self.logger.info("No prospects provided for campaign generation")
                return result
            
            if not isinstance(prospects, list):
                error_msg = "Invalid prospects data type - expected list"
                self.logger.error(error_msg)
                result.errors.append(error_msg)
                return result
            
            # Filter out invalid prospects
            valid_prospects = []
            for prospect in prospects:
                if not isinstance(prospect, dict):
                    self.logger.warning("Skipping invalid prospect - not a dictionary")
                    continue
                
                if not prospect.get('domain'):
                    self.logger.warning("Skipping prospect without domain")
                    continue
                
                if 'pain_score' not in prospect:
                    self.logger.warning(f"Skipping prospect {prospect['domain']} - missing pain_score")
                    continue
                
                valid_prospects.append(prospect)
            
            if not valid_prospects:
                self.logger.warning("No valid prospects found after validation")
                return result
            
            self.logger.info(f"Generating campaigns for {len(valid_prospects)} valid prospects...")
            
            # Sort by pain score - highest first
            valid_prospects.sort(key=lambda x: x.get('pain_score', 0), reverse=True)
            
            for prospect in valid_prospects:
                if self._shutdown_requested.is_set():
                    self.logger.info("Shutdown requested during campaign generation")
                    break
                
                if self.daily_limit_remaining <= 0:
                    self.logger.info("Daily campaign limit reached")
                    break
                
                try:
                    # Get company info with proper validation
                    company_results = self.clay_client.query_table(
                        'company_universe',
                        {'domain': prospect['domain']}
                    )
                    
                    if not company_results:
                        error_msg = f"No company found for domain: {prospect['domain']}"
                        self.logger.warning(error_msg)
                        result.errors.append(error_msg)
                        continue
                    
                    company = company_results[0]
                    
                    # Special handling for ransomware victims with enhanced error handling
                    if prospect.get('primary_edp') == SignalType.ACTIVE_RANSOMWARE.value:
                        # Get ransomware details
                        signals = self.clay_client.query_table(
                            'pain_signals',
                            {'domain': prospect['domain'], 'signal_type': SignalType.ACTIVE_RANSOMWARE.value}
                        )
                        
                        if signals and signals[0].get('raw_data'):
                            try:
                                raw_data = json.loads(signals[0]['raw_data'])
                                prospect['ransomware_group'] = raw_data.get('ransomware_group', 'Unknown')
                                prospect['hours_since_posting'] = raw_data.get('hours_since_posting', 0)
                            except (json.JSONDecodeError, KeyError) as e:
                                self.logger.error(f"Error parsing ransomware data for {prospect['domain']}: {e}")
                                prospect['ransomware_group'] = 'Unknown'
                                prospect['hours_since_posting'] = 0
                        else:
                            prospect['ransomware_group'] = 'Unknown'
                            prospect['hours_since_posting'] = 0
                        
                        self.logger.warning(
                            f"Generating URGENT campaign for ransomware victim: {company.get('company_name', 'Unknown Company')}"
                        )
                    
                    # Generate campaigns
                    campaigns = self.campaign_gen.generate_campaign(company, prospect)
                    
                    # Push to Clay outreach queue
                    for campaign in campaigns:
                        self.clay_client.add_row('outreach_queue', campaign)
                        result.campaigns_created += 1
                        self.daily_limit_remaining -= 1
                        
                        self.logger.info(
                            f"Campaign created for {company.get('company_name', 'Unknown')} - "
                            f"Type: {campaign.get('campaign_type', 'Unknown')}"
                        )
                    
                    result.prospects_processed += 1
                    
                except Exception as e:
                    error_msg = f"Campaign generation error for {prospect['domain']}: {e}"
                    self.logger.error(error_msg)
                    result.errors.append(error_msg)
            
            self.logger.info(
                f"Campaign generation complete: {result.campaigns_created} campaigns created, "
                f"{result.prospects_processed} prospects processed, {len(result.errors)} errors"
            )
            
            self.stats['total_campaigns_created'] += result.campaigns_created
            return result
    
    def check_urgent_signals(self) -> None:
        """Check for urgent signals that need immediate attention"""
        with self._error_context("urgent signals check"):
            # Collect fresh threat data
            self._collect_threat_data()
            
            # Get unprocessed ransomware signals
            urgent_companies = self.clay_client.query_table(
                'pain_signals',
                {
                    'signal_type': SignalType.ACTIVE_RANSOMWARE.value, 
                    'processed': False
                }
            )
            
            if not urgent_companies:
                return
            
            self.logger.warning(f"Found {len(urgent_companies)} URGENT ransomware victims!")
            
            # Create urgent prospects
            urgent_prospects = []
            for signal in urgent_companies:
                score_data = {
                    'domain': signal['domain'],
                    'pain_score': 100,
                    'primary_edp': SignalType.ACTIVE_RANSOMWARE.value,
                    'segment': 'post_breach_survivor',
                    'recommendation': 'immediate_outreach_critical'
                }
                urgent_prospects.append(score_data)
                
                # Mark as processed
                try:
                    self.clay_client.add_row('pain_signals', {
                        'signal_id': signal.get('signal_id'),
                        'processed': True
                    })
                except Exception as e:
                    self.logger.error(f"Error marking signal as processed: {e}")
            
            # Generate campaigns immediately
            if urgent_prospects:
                self.generate_campaigns(urgent_prospects)
    
    def run_full_cycle(self) -> None:
        """Run complete collection -> scoring -> campaign cycle"""
        cycle_start = datetime.now()
        self.logger.info("=" * 60)
        self.logger.info(f"Starting full outreach cycle at {cycle_start}")
        
        try:
            # Reset daily limit
            self.daily_limit_remaining = config.OUTREACH_DAILY_LIMIT
            
            # Step 1: Collect data
            collection_results = self.run_daily_collection()
            
            # Step 2: Score companies
            qualified_prospects = self.score_new_companies()
            
            # Step 3: Generate campaigns
            campaign_result = self.generate_campaigns(qualified_prospects)
            
            # Update statistics
            self.stats['cycles_completed'] += 1
            
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            self.logger.info(f"Full cycle completed in {cycle_duration:.2f}s")
            self.logger.info(f"Cycle statistics: {self.stats}")
            
        except Exception as e:
            self.logger.error(f"Error in full cycle: {e}", exc_info=True)
            self.stats['total_errors'] += 1
        finally:
            self.logger.info("=" * 60)
    
    def start_scheduler(self) -> None:
        """Start the automated scheduler with graceful shutdown support"""
        # Schedule jobs
        schedule.every().day.at("06:00").do(self.run_full_cycle)
        schedule.every().day.at("14:00").do(self.run_full_cycle)
        
        # Urgent checks every 2 hours
        schedule.every(2).hours.do(self.check_urgent_signals)
        
        # Additional scoring runs
        schedule.every().day.at("10:00").do(self.score_new_companies)
        schedule.every().day.at("16:00").do(self.score_new_companies)
        
        self.logger.info("Scheduler started. Running initial cycle...")
        
        # Run initial cycle
        try:
            self.run_full_cycle()
        except Exception as e:
            self.logger.error(f"Initial cycle failed: {e}")
        
        # Main scheduler loop with graceful shutdown
        self.logger.info("Entering main scheduler loop...")
        while not self._shutdown_requested.is_set():
            try:
                schedule.run_pending()
                # Use shutdown event timeout instead of sleep
                self._shutdown_requested.wait(timeout=self.SCHEDULER_CHECK_INTERVAL)
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                time.sleep(self.SCHEDULER_CHECK_INTERVAL)
        
        self.logger.info("Scheduler stopped")
    
    def cleanup(self) -> None:
        """Cleanup resources"""
        self.logger.info("Performing cleanup...")
        # Add any necessary cleanup code here
        # e.g., close database connections, save state, etc.


def main():
    """Main entry point with proper error handling"""
    logger = LoggerSetup.configure_logging()
    
    try:
        orchestrator = BTAOrchestrator()
        
        # For testing, uncomment the line below:
        # orchestrator.run_full_cycle()
        
        # For production, start scheduler
        orchestrator.start_scheduler()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}", exc_info=True)
        sys.exit(1)
    finally:
        try:
            orchestrator.cleanup()
        except NameError:
            pass  # orchestrator wasn't created yet
        logger.info("Application shutdown complete")


if __name__ == "__main__":
    main()
