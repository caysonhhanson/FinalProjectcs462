from src.scrapers.craigslist_scraper import CraigslistScraper
from src.database.db import Database

class ScraperManager:
    def __init__(self):
        self.db = Database()
        self.cl_scraper = CraigslistScraper(city="saltlakecity")
    
    def run_scrape(self, max_pages=2):
        """Run full scrape and store in database"""
        print("🚀 Starting scrape job...\n")
        
        # Scrape listings
        listings = self.cl_scraper.scrape_listings(max_pages=max_pages)
        
        if not listings:
            print("⚠️ No listings found. Craigslist may have changed their HTML structure.")
            print("   Let's check the page manually...")
            return
        
        # Store in database
        new_count = 0
        updated_count = 0
        price_changes = 0
        
        for listing in listings:
            try:
                # Insert or update listing
                result = self.db.insert_listing(listing)
                
                if result:
                    listing_id = result[0]['id']
                    new_price = result[0]['price']
                    
                    # Check if this is a new listing or price changed
                    price_history_check = self.db.execute_query(
                        "SELECT COUNT(*) as count FROM price_history WHERE listing_id = %s;",
                        (listing_id,),
                        fetch=True
                    )
                    
                    if price_history_check[0]['count'] == 0:
                        # New listing - add initial price to history
                        new_count += 1
                        self.db.insert_price_history(listing_id, new_price)
                    else:
                        # Existing listing - check for price change
                        updated_count += 1
                        
                        # Get the most recent price from history
                        last_price_query = """
                        SELECT price FROM price_history 
                        WHERE listing_id = %s 
                        ORDER BY recorded_at DESC 
                        LIMIT 1;
                        """
                        last_price_result = self.db.execute_query(
                            last_price_query,
                            (listing_id,),
                            fetch=True
                        )
                        
                        if last_price_result:
                            last_price = last_price_result[0]['price']
                            if last_price != new_price:
                                # Price changed!
                                price_changes += 1
                                self.db.insert_price_history(listing_id, new_price)
                                print(f"  💰 Price change: {listing['title']}")
                                print(f"     ${float(last_price):,.2f} → ${float(new_price):,.2f}")
                        
            except Exception as e:
                print(f"  ❌ Error storing listing: {e}")
                continue
        
        print(f"\n✅ Scrape complete!")
        print(f"   📊 New listings: {new_count}")
        print(f"   🔄 Updated listings: {updated_count}")
        print(f"   💵 Price changes: {price_changes}")
    
    def get_stats(self):
        """Get database statistics"""
        total = self.db.execute_query(
            "SELECT COUNT(*) as count FROM listings;",
            fetch=True
        )[0]['count']
        
        active = self.db.execute_query(
            "SELECT COUNT(*) as count FROM listings WHERE is_active = TRUE;",
            fetch=True
        )[0]['count']
        
        price_records = self.db.execute_query(
            "SELECT COUNT(*) as count FROM price_history;",
            fetch=True
        )[0]['count']
        
        print(f"\n📈 Database Stats:")
        print(f"   Total listings: {total}")
        print(f"   Active listings: {active}")
        print(f"   Price history records: {price_records}")
    
    def close(self):
        """Close database connection"""
        self.db.close()


if __name__ == "__main__":
    manager = ScraperManager()
    
    # Run scrape
    manager.run_scrape(max_pages=2)
    
    # Show stats
    manager.get_stats()
    
    # Close connection
    manager.close()
