import psycopg
from psycopg.rows import dict_row
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.conn = None
        self.connect()
    
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            # psycopg3 connection string format
            conninfo = f"host={os.getenv('DB_HOST', 'localhost')} " \
                      f"dbname={os.getenv('DB_NAME', 'carwatch')} " \
                      f"user={os.getenv('DB_USER', os.getenv('USER'))} " \
                      f"password={os.getenv('DB_PASSWORD', '')} " \
                      f"port={os.getenv('DB_PORT', '5432')}"
            
            self.conn = psycopg.connect(conninfo)
            print("✅ Database connection successful")
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
            print(f"❌ Query failed: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("Database connection closed")

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
