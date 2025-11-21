from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from src.scrapers.scraper_manager import ScraperManager
from src.utils.logger import setup_logger
from datetime import datetime
import sys

logger = setup_logger('scheduler')

def run_daily_scrape():
    """Run the daily scrape job"""
    logger.info("*" * 70)
    logger.info(f"SCHEDULED JOB TRIGGERED - {datetime.now()}")
    logger.info("*" * 70)
    
    manager = ScraperManager()
    try:
        # Run scrape with 2 pages (adjust as needed)
        manager.run_scrape(max_pages=2)
        manager.get_stats()
    except Exception as e:
        logger.error(f"Scheduled job failed: {e}", exc_info=True)
    finally:
        manager.close()

def start_scheduler(test_mode=False):
    """Start the scheduler"""
    scheduler = BlockingScheduler()
    
    if test_mode:
        # For testing: run every minute
        logger.info("🧪 TEST MODE: Scheduler will run every minute")
        scheduler.add_job(
            run_daily_scrape,
            'interval',
            minutes=1,
            id='test_scrape',
            name='Test Scrape (every minute)'
        )
    else:
        # Production: run every day at 2 AM
        logger.info("📅 PRODUCTION MODE: Scheduler will run daily at 2:00 AM")
        scheduler.add_job(
            run_daily_scrape,
            CronTrigger(hour=2, minute=0),  # 2:00 AM daily
            id='daily_scrape',
            name='Daily Car Scrape',
            replace_existing=True
        )
    
    # Run immediately on startup
    logger.info("🚀 Running initial scrape now...")
    run_daily_scrape()
    
    # Start scheduler
    logger.info("⏰ Scheduler started. Press Ctrl+C to exit.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='CarWatch Scheduler')
    parser.add_argument('--test', action='store_true', help='Run in test mode (every minute)')
    args = parser.parse_args()
    
    start_scheduler(test_mode=args.test)
