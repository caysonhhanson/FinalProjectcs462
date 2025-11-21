from src.database.db import Database

def test_connection():
    print("Testing database connection...")
    db = Database()
    
    # Test query
    result = db.execute_query("SELECT COUNT(*) as count FROM listings;", fetch=True)
    print(f"✅ Listings table exists! Current count: {result[0]['count']}")
    
    db.close()

if __name__ == "__main__":
    test_connection()
