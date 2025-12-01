import psycopg

DATABASE_URL = "postgresql://carwatch:IXg22h9juSWEJxD0c8HxFNaXV34FILoq@dpg-d4mtcajuibrs738ssirg-a.oregon-postgres.render.com/carwatch"

conn = psycopg.connect(DATABASE_URL)
cur = conn.cursor()

print("Checking all alerts in database:\n")

cur.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT 5")
alerts = cur.fetchall()

print(f"Found {len(alerts)} alerts:")
for alert in alerts:
    print(alert)

conn.close()