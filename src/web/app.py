from flask import Flask, render_template, request, jsonify
from src.database.db import Database
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

def get_db():
    """Get database connection"""
    return Database()

@app.route('/')
def index():
    """Home page - search interface"""
    print("📄 Loading index page")
    return render_template('index.html')

@app.route('/api/listings')
def get_listings():
    """API endpoint to get listings with filters"""
    print(f"🔍 API call to /api/listings with args: {request.args}")
    
    try:
        db = get_db()
        
        # Get filter parameters
        search = request.args.get('search', '').strip()
        make = request.args.get('make', '').strip()
        model = request.args.get('model', '').strip()
        min_year = request.args.get('min_year', type=int)
        max_year = request.args.get('max_year', type=int)
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        max_mileage = request.args.get('max_mileage', type=int)
        sort_by = request.args.get('sort_by', 'updated_at')
        sort_order = request.args.get('sort_order', 'DESC')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Build WHERE clause
        where_clause = "WHERE is_active = TRUE"
        params = []
        
        # Add filters
        if search:
            where_clause += " AND (title ILIKE %s OR make ILIKE %s OR model ILIKE %s)"
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern, search_pattern])
        
        if make:
            where_clause += " AND make ILIKE %s"
            params.append(f"%{make}%")
        
        if model:
            where_clause += " AND model ILIKE %s"
            params.append(f"%{model}%")
        
        if min_year:
            where_clause += " AND year >= %s"
            params.append(min_year)
        
        if max_year:
            where_clause += " AND year <= %s"
            params.append(max_year)
        
        if min_price:
            where_clause += " AND price >= %s"
            params.append(min_price)
        
        if max_price:
            where_clause += " AND price <= %s"
            params.append(max_price)
        
        if max_mileage:
            where_clause += " AND mileage <= %s"
            params.append(max_mileage)
        
        # Get total count first
        count_query = f"SELECT COUNT(*) as count FROM listings {where_clause}"
        total_count = db.execute_query(count_query, tuple(params), fetch=True)[0]['count']
        
        print(f"📈 Total count: {total_count}")
        
        # Build main query with sorting and pagination
        valid_sort_fields = ['price', 'year', 'mileage', 'updated_at', 'first_seen']
        if sort_by not in valid_sort_fields:
            sort_by = 'updated_at'
        
        if sort_order.upper() not in ['ASC', 'DESC']:
            sort_order = 'DESC'
        
        query = f"""
            SELECT 
                id, external_id, source, url, title, price, year, 
                make, model, mileage, location, first_seen, last_seen, is_active
            FROM listings
            {where_clause}
            ORDER BY {sort_by} {sort_order}
            LIMIT %s OFFSET %s
        """
        
        # Add pagination params
        offset = (page - 1) * per_page
        query_params = params + [per_page, offset]
        
        print(f"📊 Executing query with {len(query_params)} parameters")
        
        # Execute query
        listings = db.execute_query(query, tuple(query_params), fetch=True)
        
        print(f"✅ Found {len(listings)} listings")
        
        db.close()
        
        # Convert datetime objects to strings for JSON serialization
        for listing in listings:
            if listing.get('first_seen'):
                listing['first_seen'] = listing['first_seen'].isoformat()
            if listing.get('last_seen'):
                listing['last_seen'] = listing['last_seen'].isoformat()
        
        return jsonify({
            'listings': listings,
            'total': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })
        
    except Exception as e:
        print(f"❌ Error in /api/listings: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/listing/<int:listing_id>')
def get_listing_detail(listing_id):
    """Get detailed information about a specific listing"""
    db = get_db()
    
    # Get listing info
    listing_query = "SELECT * FROM listings WHERE id = %s"
    listing = db.execute_query(listing_query, (listing_id,), fetch=True)
    
    if not listing:
        db.close()
        return jsonify({'error': 'Listing not found'}), 404
    
    listing = listing[0]
    
    # Get price history
    price_history_query = """
        SELECT price, recorded_at 
        FROM price_history 
        WHERE listing_id = %s 
        ORDER BY recorded_at ASC
    """
    price_history = db.execute_query(price_history_query, (listing_id,), fetch=True)
    
    db.close()
    
    # Convert datetime objects
    if listing.get('first_seen'):
        listing['first_seen'] = listing['first_seen'].isoformat()
    if listing.get('last_seen'):
        listing['last_seen'] = listing['last_seen'].isoformat()
    if listing.get('created_at'):
        listing['created_at'] = listing['created_at'].isoformat()
    if listing.get('updated_at'):
        listing['updated_at'] = listing['updated_at'].isoformat()
    
    for record in price_history:
        if record.get('recorded_at'):
            record['recorded_at'] = record['recorded_at'].isoformat()
    
    return jsonify({
        'listing': listing,
        'price_history': price_history
    })

@app.route('/api/stats')
def get_stats():
    """Get database statistics"""
    db = get_db()
    stats = db.get_stats()
    
    # Get makes distribution
    makes_query = """
        SELECT make, COUNT(*) as count 
        FROM listings 
        WHERE is_active = TRUE AND make IS NOT NULL
        GROUP BY make 
        ORDER BY count DESC 
        LIMIT 10
    """
    top_makes = db.execute_query(makes_query, fetch=True)
    stats['top_makes'] = top_makes
    
    # Get price statistics
    price_stats_query = """
        SELECT 
            MIN(price) as min_price,
            MAX(price) as max_price,
            AVG(price) as avg_price,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) as median_price
        FROM listings
        WHERE is_active = TRUE AND price IS NOT NULL
    """
    price_stats = db.execute_query(price_stats_query, fetch=True)[0]
    stats.update(price_stats)
    
    db.close()
    
    return jsonify(stats)

@app.route('/listing/<int:listing_id>')
def listing_detail(listing_id):
    """Listing detail page"""
    return render_template('listing_detail.html', listing_id=listing_id)

@app.route('/stats')
def stats_page():
    """Statistics page"""
    return render_template('stats.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
