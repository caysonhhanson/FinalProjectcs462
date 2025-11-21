from src.scrapers.craigslist_scraper import CraigslistScraper
from src.database.db import Database
from src.utils.logger import setup_logger
from datetime import datetime

class ScraperManager:
    def __init__(self):
        self.logger = setup_logger('scraper_manager')
        self.db = Database()
        self.cl_scraper = CraigslistScraper(city="saltlakecity")
        self.logger.info("ScraperManager initialized")
    
    def run_scrape(self, max_pages=2):
        """Run full scrape and store in database"""
        start_time = datetime.now()
        self.logger.info("="*60)
        self.logger.info(f"Starting scrape job at {start_time}")
        self.logger.info("="*60)
        
        try:
            # Scrape listings
            listings = self.cl_scraper.scrape_listings(max_pages=max_pages)
            
            if not listings:
                self.logger.warning("No listings found!")
                return
            
            self.logger.info(f"Scraped {len(listings)} total listings")
            
            # Get currently active listings to detect removals
            current_external_ids = {listing['external_id'] for listing in listings}
            
            # Process each listing
            stats = {
                'new': 0,
                'updated': 0,
                'price_increases': 0,
                'price_decreases': 0,
                'errors': 0
            }
            
            for listing in listings:
                try:
                    self._process_listing(listing, stats)
                except Exception as e:
                    stats['errors'] += 1
                    self.logger.error(f"Error processing listing {listing.get('title', 'Unknown')}: {e}")
            
            # Mark stale listings as inactive (not seen in 7 days)
            stale = self.db.mark_stale_listings_inactive(days=7)
            if stale:
                self.logger.info(f"Marked {len(stale)} listings as inactive")
            
            # Log final stats
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info("="*60)
            self.logger.info("Scrape Complete!")
            self.logger.info(f"  Duration: {duration:.1f} seconds")
            self.logger.info(f"  New listings: {stats['new']}")
            self.logger.info(f"  Updated listings: {stats['updated']}")
            self.logger.info(f"  Price increases: {stats['price_increases']}")
            self.logger.info(f"  Price decreases: {stats['price_decreases']}")
            if stats['errors'] > 0:
                self.logger.warning(f"  Errors: {stats['errors']}")
            self.logger.info("="*60)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Scrape job failed: {e}", exc_info=True)
            raise
    
    def _process_listing(self, listing, stats):
        """Process a single listing and update stats"""
        # Insert or update listing
        result = self.db.insert_listing(listing)
        
        if not result:
            return
        
        listing_id = result[0]['id']
        current_price = result[0]['price']
        
        # Check if this is a new listing
        if not self.db.has_price_history(listing_id):
            # New listing
            stats['new'] += 1
            self.db.insert_price_history(listing_id, current_price)
            self.logger.info(f"NEW: {listing['title']} - ${current_price:,.2f}")
        else:
            # Existing listing - check for price change
            stats['updated'] += 1
            last_price = self.db.get_last_price_from_history(listing_id)
            
            if last_price and current_price and last_price != current_price:
                # Price changed!
                self.db.insert_price_history(listing_id, current_price)
                
                price_diff = float(current_price) - float(last_price)
                percent_change = (price_diff / float(last_price)) * 100
                
                if price_diff > 0:
                    stats['price_increases'] += 1
                    self.logger.info(
                        f"PRICE UP: {listing['title']} - "
                        f"${float(last_price):,.2f} → ${float(current_price):,.2f} "
                        f"(+${price_diff:,.2f}, +{percent_change:.1f}%)"
                    )
                else:
                    stats['price_decreases'] += 1
                    self.logger.info(
                        f"PRICE DOWN: {listing['title']} - "
                        f"${float(last_price):,.2f} → ${float(current_price):,.2f} "
                        f"(${price_diff:,.2f}, {percent_change:.1f}%)"
                    )
    
    def get_stats(self):
        """Get and display database statistics"""
        stats = self.db.get_stats()
        
        self.logger.info("\n" + "="*60)
        self.logger.info("Database Statistics")
        self.logger.info("="*60)
        self.logger.info(f"  Total listings: {stats['total_listings']}")
        self.logger.info(f"  Active listings: {stats['active_listings']}")
        self.logger.info(f"  Inactive listings: {stats['inactive_listings']}")
        self.logger.info(f"  Price history records: {stats['price_records']}")
        self.logger.info(f"  Listings with price changes: {stats['listings_with_changes']}")
        self.logger.info("="*60 + "\n")
        
        return stats
    
    def close(self):
        """Close database connection"""
        self.db.close()
        self.logger.info("Database connection closed")


if __name__ == "__main__":
    manager = ScraperManager()
    
    try:
        # Run scrape
        manager.run_scrape(max_pages=2)
        
        # Show stats
        manager.get_stats()
    finally:
        # Always close connection
        manager.close()
