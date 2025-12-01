import psycopg

DATABASE_URL = "postgresql://carwatch:IXg22h9juSWEJxD0c8HxFNaXV34FILoq@dpg-d4mtcajuibrs738ssirg-a.oregon-postgres.render.com/carwatch"

print("🔌 Connecting to Render database...")
try:
    conn = psycopg.connect(DATABASE_URL)
    cur = conn.cursor()
    
    print("📋 Creating schema...")
    
    # Read schema file
    with open('src/database/schema.sql', 'r') as f:
        schema = f.read()
    
    # Execute schema
    cur.execute(schema)
    conn.commit()
    
    print("✅ Schema created successfully!")
    
    # Verify tables were created
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    
    tables = cur.fetchall()
    print(f"\n📊 Created {len(tables)} tables:")
    for table in tables:
        print(f"   ✓ {table[0]}")
    
    conn.close()
    print("\n🎉 Database setup complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    