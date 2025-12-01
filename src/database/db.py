import psycopg
from psycopg.rows import dict_row
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

class Database:
    def __init__(self):
        self.conn = None
        self.connect()
    
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            # Check if we're on Render (uses DATABASE_URL)
            database_url = os.getenv('DATABASE_URL')
            
            if database_url:
                # Production (Render)
                self.conn = psycopg.connect(database_url)
            else:
                # Local development
                conninfo = f"host={os.getenv('DB_HOST', 'localhost')} " \
                          f"dbname={os.getenv('DB_NAME', 'carwatch')} " \
                          f"user={os.getenv('DB_USER', os.getenv('USER'))} " \
                          f"password={os.getenv('DB_PASSWORD', '')} " \
                          f"port={os.getenv('DB_PORT', '5432')}"
                
                self.conn = psycopg.connect(conninfo)
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise
    
    def execute_query(self, query, params=None, fetch=False):
        """Execute a SQL query"""
        try:
            with self.conn.cursor(row_factory=dict_row) as cur:
                cur.execute(query, params)
                if fetch:
                    return cur.fetchall()
                self.conn.commit()
                return cur.rowcount
        except Exception as e:
            self.conn.rollback()
            raise
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def insert_listing(self, listing_data):
        """Insert or update a listing"""
        query = """
        INSERT INTO listings (
            external_id, source, url, title, price, year, 
            make, model, mileage, location, description
        ) VALUES (
            %(external_id)s, %(source)s, %(url)s, %(title)s, %(price)s, %(year)s,
            %(make)s, %(model)s, %(mileage)s, %(location)s, %(description)s
        )
        ON CONFLICT (external_id) DO UPDATE SET
            price = EXCLUDED.price,
            last_seen = NOW(),
            updated_at = NOW()
        RETURNING id, price;
        """
        return self.execute_query(query, listing_data, fetch=True)
    
    def insert_price_history(self, listing_id, price):
        """Insert price history record"""
        query = """
        INSERT INTO price_history (listing_id, price)
        VALUES (%s, %s);
        """
        return self.execute_query(query, (listing_id, price))
    
    def get_listing_current_price(self, listing_id):
        """Get current price of a listing"""
        query = "SELECT price FROM listings WHERE id = %s;"
        result = self.execute_query(query, (listing_id,), fetch=True)
        return result[0]['price'] if result else None
    
    def get_last_price_from_history(self, listing_id):
        """Get the most recent price from price history"""
        query = """
        SELECT price FROM price_history 
        WHERE listing_id = %s 
        ORDER BY recorded_at DESC 
        LIMIT 1;
        """
        result = self.execute_query(query, (listing_id,), fetch=True)
        return result[0]['price'] if result else None
    
    def has_price_history(self, listing_id):
        """Check if listing has any price history"""
        query = "SELECT COUNT(*) as count FROM price_history WHERE listing_id = %s;"
        result = self.execute_query(query, (listing_id,), fetch=True)
        return result[0]['count'] > 0
    
    def mark_stale_listings_inactive(self, days=7):
        """Mark listings as inactive if not seen in X days"""
        query = """
        UPDATE listings 
        SET is_active = FALSE 
        WHERE last_seen < NOW() - INTERVAL '%s days' 
        AND is_active = TRUE
        RETURNING id, title;
        """
        return self.execute_query(query, (days,), fetch=True)
    
    def get_all_active_external_ids(self):
        """Get all external IDs of currently active listings"""
        query = "SELECT external_id FROM listings WHERE is_active = TRUE;"
        results = self.execute_query(query, fetch=True)
        return {row['external_id'] for row in results}
    
    def get_stats(self):
        """Get database statistics"""
        stats = {}
        
        # Total listings
        result = self.execute_query("SELECT COUNT(*) as count FROM listings;", fetch=True)
        stats['total_listings'] = result[0]['count']
        
        # Active listings
        result = self.execute_query(
            "SELECT COUNT(*) as count FROM listings WHERE is_active = TRUE;",
            fetch=True
        )
        stats['active_listings'] = result[0]['count']
        
        # Inactive listings
        stats['inactive_listings'] = stats['total_listings'] - stats['active_listings']
        
        # Price history records
        result = self.execute_query("SELECT COUNT(*) as count FROM price_history;", fetch=True)
        stats['price_records'] = result[0]['count']
        
        # Listings with price changes
        result = self.execute_query("""
            SELECT COUNT(DISTINCT listing_id) as count 
            FROM price_history 
            GROUP BY listing_id 
            HAVING COUNT(*) > 1;
        """, fetch=True)
        stats['listings_with_changes'] = result[0]['count'] if result else 0
        
        return stats
