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
            
            self.check_alerts()

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

    def check_alerts(self):
        """Check for alert matches after scraping"""
        self.logger.info("🔔 Checking for alert matches...")
    
        # Get all active alerts
        alerts_query = "SELECT * FROM alerts WHERE is_active = TRUE"
        alerts = self.db.execute_query(alerts_query, fetch=True)
    
        if not alerts:
            self.logger.info("No active alerts to check")
            return
    
        matches_found = 0
    
        for alert in alerts:
            # Build query to find matching listings
            query = """
                SELECT l.*, COUNT(am.id) as already_notified
                FROM listings l
                LEFT JOIN alert_matches am ON l.id = am.listing_id AND am.alert_id = %s
                WHERE l.is_active = TRUE
            """
            params = [alert['id']]
        
            # Add criteria filters
            if alert['make']:
                query += " AND l.make ILIKE %s"
                params.append(f"%{alert['make']}%")
        
            if alert['model']:
                query += " AND l.model ILIKE %s"
                params.append(f"%{alert['model']}%")
        
            if alert['min_year']:
                query += " AND l.year >= %s"
                params.append(alert['min_year'])
        
            if alert['max_year']:
                query += " AND l.year <= %s"
                params.append(alert['max_year'])
        
            if alert['max_price']:
                query += " AND l.price <= %s"
                params.append(alert['max_price'])
        
            if alert['max_mileage']:
                query += " AND l.mileage <= %s"
                params.append(alert['max_mileage'])
        
            query += " GROUP BY l.id HAVING COUNT(am.id) = 0"  # Only new matches
        
            matching_listings = self.db.execute_query(query, tuple(params), fetch=True)
        
            if matching_listings:
                self.logger.info(f"Found {len(matching_listings)} matches for alert {alert['id']}")
            
                # Record matches
                for listing in matching_listings:
                    match_query = """
                        INSERT INTO alert_matches (alert_id, listing_id)
                        VALUES (%s, %s)
                    """
                    self.db.execute_query(match_query, (alert['id'], listing['id']))
                    matches_found += 1
            
                # Send email notification
                self._send_alert_email(alert, matching_listings)
    
        self.logger.info(f"✅ Alert check complete: {matches_found} new matches")



def _send_alert_email(self, alert, listings):
    """Send email notification for alert matches"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import os
        
        # Email configuration (you'll need to set these in .env)
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        sender_email = os.getenv('SENDER_EMAIL')
        sender_password = os.getenv('SENDER_PASSWORD')
        
        if not sender_email or not sender_password:
            self.logger.warning("Email credentials not configured - skipping notification")
            return
        
        # Build email content
        subject = f"🚗 CarWatch Alert: {len(listings)} new cars match your criteria!"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #667eea;">New Cars Found!</h2>
            <p>We found {len(listings)} cars matching your alert:</p>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <strong>Your Alert Criteria:</strong><br>
                {f"Make: {alert['make']}<br>" if alert['make'] else ""}
                {f"Model: {alert['model']}<br>" if alert['model'] else ""}
                {f"Year: {alert['min_year']}-{alert['max_year']}<br>" if alert['min_year'] or alert['max_year'] else ""}
                Max Price: ${float(alert['max_price']):,.2f}<br>
                {f"Max Mileage: {int(alert['max_mileage']):,} mi<br>" if alert['max_mileage'] else ""}
            </div>
            
            <h3>Matching Cars:</h3>
        """
        
        for listing in listings[:10]:  # Limit to 10 in email
            price_str = f"${float(listing['price']):,.2f}" if listing['price'] else "N/A"
            mileage_str = f"{int(listing['mileage']):,} mi" if listing['mileage'] else "N/A"
            
            body += f"""
            <div style="border-left: 4px solid #667eea; padding: 15px; margin: 15px 0; background: white;">
                <h4 style="margin: 0 0 10px 0;">{listing['title']}</h4>
                <p style="margin: 5px 0;">
                    💰 <strong>{price_str}</strong> | 
                    🛣️ {mileage_str} | 
                    📍 {listing['location'] or 'Location N/A'}
                </p>
                <a href="{listing['url']}" style="color: #667eea; text-decoration: none;">View Listing →</a>
            </div>
            """
        
        if len(listings) > 10:
            body += f"<p><em>...and {len(listings) - 10} more!</em></p>"
        
        body += """
            <hr style="margin: 30px 0;">
            <p style="color: #666; font-size: 0.9rem;">
                You're receiving this because you created a price alert on CarWatch.<br>
                To manage your alerts, visit <a href="http://127.0.0.1:5000/alerts">CarWatch Alerts</a>
            </p>
        </body>
        </html>
        """
        
        # Create message
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = sender_email
        message['To'] = alert['email']
        
        message.attach(MIMEText(body, 'html'))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
        
        self.logger.info(f"📧 Email sent to {alert['email']}")
        
    except Exception as e:
        self.logger.error(f"Failed to send email: {e}")

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
