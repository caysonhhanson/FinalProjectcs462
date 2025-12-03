# CarWatch - Final Project Report
**CS 462 - Fall 2025**  
**Used Car Price Tracker & Alert System**

---

## Project Summary

CarWatch is a full-stack web application that automatically scrapes used car listings from Craigslist, tracks price changes over time, and sends email notifications when cars matching user-defined criteria are found. The system runs daily automated scrapes, stores historical pricing data, and provides interactive visualizations for market analysis.

**Key Technologies:** Python, Flask, PostgreSQL, BeautifulSoup, APScheduler, Chart.js, Render (deployment)

**Live Demo:** [https://finalprojectcs462-1.onrender.com]

---

## Project Highlights

###  Core Features Implemented

1. **Automated Web Scraping**
   - Daily scraping of Craigslist Salt Lake City car listings
   - Intelligent parsing of make, model, year, price, mileage
   - Duplicate detection using external listing IDs
   - Stale listing detection (marks inactive after 7 days)

2. **Price History Tracking**
   - Automatic price change detection and logging
   - Historical price database with timestamps
   - Price increase/decrease analytics

3. **Interactive Web Interface**
   - Real-time search with filters (make, model, year, price, mileage)
   - Listing detail pages with price history charts
   - Statistics dashboard with market insights
   - Alert management system

4. **Price Alert System**
   - Custom alert criteria (make, model, year range, max price, max mileage)
   - Daily alert matching after scraping
   - Email notifications with HTML formatting
   - Alert pause/resume/delete functionality

5. **Production Deployment**
   - Deployed on Render with PostgreSQL database
   - Automated daily scraping at 2 AM
   - Persistent data storage and logging

---

##  System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CarWatch System                          │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐         
│  Craigslist SLC  │         
│   (HTML Pages)   │         
└────────┬─────────┘         
         │                   
         │ HTTP GET Requests (w/ headers)
         ▼                   
┌─────────────────────────────────────────────────┐
│         Web Scraper (Python)                     │
│  - BeautifulSoup4 for HTML parsing              │
│  - Runs every 24 hours via APScheduler          │
│  - Extracts: price, title, year, make, model    │
│  - Handles pagination (2 pages)                 │
└────────────────────┬────────────────────────────┘
                     │
                     │ INSERT/UPDATE (psycopg3)
                     ▼
┌─────────────────────────────────────────────────┐
│         PostgreSQL Database (Render)             │
│                                                  │
│  Tables:                                         │
│  • listings (500+ cars)                         │
│  • price_history (time-series)                  │
│  • alerts (user preferences)                    │
│  • alert_matches (notifications log)            │
└────────────────────┬────────────────────────────┘
                     │
                     │ SELECT queries
                     ▼
┌─────────────────────────────────────────────────┐
│       Flask Web Application                      │
│                                                  │
│  Endpoints:                                      │
│  • GET /api/listings (search & filter)          │
│  • GET /api/listing/:id (details + history)     │
│  • POST /api/alerts (create alert)              │
│  • GET /api/alerts (user's alerts)              │
│  • GET /api/stats (market statistics)           │
└────────────────────┬────────────────────────────┘
                     │
                     │ HTML/JSON Response
                     ▼
┌─────────────────────────────────────────────────┐
│          Web Frontend (Vanilla JS)              │
│                                                  │
│  Pages:                                          │
│  • Search/Browse with filters                   │
│  • Listing detail with Chart.js graphs          │
│  • Create/manage alerts                         │
│  • Statistics dashboard                         │
└─────────────────────────────────────────────────┘

         ┌──────────────────────┐
         │  Alert Notification  │
         │  System (SMTP Email) │
         │  - Checks daily      │
         │  - Matches alerts    │
         │  - HTML templates    │
         └──────────────────────┘
```

---

##  Database Schema

```
┌─────────────────────────────────────┐
│           LISTINGS                  │
├─────────────────────────────────────┤
│ PK  id                 SERIAL       │
│ UK  external_id        VARCHAR(255) │ ← Unique constraint
│     source             VARCHAR(50)  │ ← 'craigslist'
│     url                TEXT         │
│     title              TEXT         │
│     price              DECIMAL      │
│     year               INTEGER      │
│     make               VARCHAR(100) │
│     model              VARCHAR(100) │
│     mileage            INTEGER      │
│     location           VARCHAR(255) │
│     description        TEXT         │
│     first_seen         TIMESTAMP    │
│     last_seen          TIMESTAMP    │
│     is_active          BOOLEAN      │ ← Stale detection
│     created_at         TIMESTAMP    │
│     updated_at         TIMESTAMP    │
└──────────┬──────────────────────────┘
           │
           │ 1:N
           ▼
┌─────────────────────────────────────┐
│         PRICE_HISTORY               │
├─────────────────────────────────────┤
│ PK  id                 SERIAL       │
│ FK  listing_id         INTEGER      │
│     price              DECIMAL      │
│     recorded_at        TIMESTAMP    │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│           ALERTS                    │
├─────────────────────────────────────┤
│ PK  id                 SERIAL       │
│     email              VARCHAR(255) │
│     make               VARCHAR(100) │
│     model              VARCHAR(100) │
│     min_year           INTEGER      │
│     max_year           INTEGER      │
│     max_price          DECIMAL      │
│     max_mileage        INTEGER      │
│     created_at         TIMESTAMP    │
│     is_active          BOOLEAN      │
└──────────┬──────────────────────────┘
           │
           │ N:M (through alert_matches)
           ▼
┌─────────────────────────────────────┐
│        ALERT_MATCHES                │
├─────────────────────────────────────┤
│ PK  id                 SERIAL       │
│ FK  alert_id           INTEGER      │
│ FK  listing_id         INTEGER      │
│     matched_at         TIMESTAMP    │
│     notified           BOOLEAN      │
└─────────────────────────────────────┘

Indexes:
- idx_listings_external_id (for duplicate detection)
- idx_listings_is_active (for filtering active listings)
- idx_listings_make_model (for search queries)
- idx_price_history_listing_id (for price charts)
```

---

## Demo Screenshots

### 1. Search Interface
![alt text](<Screenshot 2025-12-03 at 11.39.37 AM-1.png>)
### 2. Listing Detail with Price History
![alt text](<Screenshot 2025-12-03 at 11.39.59 AM.png>)

### 3. Statistics Dashboard
![alt text](<Screenshot 2025-12-03 at 11.40.31 AM.png>)
### 4. Alert Management
![alt text](<Screenshot 2025-12-03 at 11.41.25 AM.png>)
---

## What I Learned

### Technical Skills

1. **Web Scraping Best Practices**
   - Respectful scraping with delays (2 seconds between requests)
   - User-Agent headers to avoid blocking
   - Robust HTML parsing with error handling
   - Handling dynamic content and pagination

2. **Database Design & Optimization**
   - Proper indexing for query performance
   - ON CONFLICT DO UPDATE for upserts
   - Foreign key constraints and cascading deletes
   - Time-series data modeling for price history

3. **Full-Stack Development**
   - RESTful API design with Flask
   - Frontend JavaScript (vanilla, no frameworks)
   - Chart.js for data visualization
   - Jinja2 templating for server-side rendering

4. **Production Deployment**
   - PostgreSQL on Render
   - Environment variables for secrets
   - Gunicorn for production WSGI server
   - Debugging remote database issues

### System Design Insights

1. **Concurrency & Scheduling**
   - APScheduler for cron-like job scheduling
   - Single scraper process (no race conditions)
   - Database transactions for consistency
   - Job logging for debugging

2. **Data Integrity**
   - Duplicate detection using external IDs
   - Stale listing detection (last_seen timestamp)
   - Price change detection with tolerance
   - Alert matching without duplicate notifications

3. **Scalability Considerations**
   - Designed for ~5000 listings (current: 500+)
   - Pagination for large result sets
   - Indexes on commonly queried fields
   - Future: Redis caching for hot queries

---

## AI Integration & Assistance

### How AI Was Used in Development

**Claude was used in building this project:**

   - Helped design database schema with proper relationships
   - Suggested Flask project structure and best practices
   - Recommended APScheduler for job scheduling
   - Advised on error handling patterns
   - Resolved psycopg3 transaction commit bugs
   - Debugged Render deployment configuration
   - Generated comprehensive FINAL_REPORT Template

### AI Features in the Application

**Current Implementation:**
- No AI/ML features in user-facing application
- Traditional rule-based alert matching

**Future Enhancements (Ideas):**
- **Price Prediction**: Use ML to predict when prices will drop
- **Smart Alerts**: Recommend alert criteria based on market trends
- **Anomaly Detection**: Flag suspiciously low prices (potential scams)
- **NLP Search**: Natural language queries like "reliable family SUV under $20k"
- **Image Recognition**: Analyze car photos for condition assessment

---

## Why This Project Is Interesting

### Personal Motivation

As someone who has bought used cars before, I've experienced the frustration of:
- Missing great deals because I didn't check listings daily
- Not knowing if a price is actually good or inflated
- Wasting time on overpriced or already-sold listings
- No easy way to track price drops

CarWatch solves these real-world problems with automation!

### Technical Interest

This project combines multiple CS concepts I wanted to explore:
- **Web scraping**: Navigating the legal/ethical considerations
- **Time-series data**: Modeling price changes over time
- **Scheduled jobs**: Building reliable background processes
- **Full-stack dev**: End-to-end ownership of a product
- **Data visualization**: Making data actionable for users

### Real-World Impact

CarWatch could help:
- **Car buyers**: Find the best deals and negotiate from a position of knowledge
- **Market researchers**: Analyze used car market trends
- **Sellers**: Price their cars competitively based on market data
- **Economists**: Study inflation and depreciation patterns

---

## Key Learnings

### 1. Data Quality is Paramount

**Challenge:** Craigslist HTML is inconsistent. Some listings have mileage, others don't. Some prices include "$", others are just numbers.

**Solution:** Built robust parsing with fallbacks:
```python
def _parse_mileage(self, text):
    """Extract mileage with multiple patterns"""
    match = re.search(r'([\d,]+)k?\s*(miles?|mi)', text.lower())
    if match:
        mileage = float(match.group(1).replace(',', ''))
        if 'k' in match.group(0).lower():
            mileage *= 1000
        return int(mileage)
    return None  # Graceful degradation
```

**Lesson:** Never assume data will be clean. Always handle `None` values, provide defaults, and log anomalies.

---

### 2. Transactions & Commits Matter

**Bug:** Price history wasn't being recorded. Queries returned empty results even though `INSERT` succeeded.

**Root Cause:** Forgot to call `conn.commit()` BEFORE returning results from `execute_query()`.

**Fix:**
```python
def execute_query(self, query, params=None, fetch=False):
    try:
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params)
            if fetch:
                result = cur.fetchall()
                self.conn.commit()  # ✅ COMMIT BEFORE RETURNING!
                return result
            self.conn.commit()
```

**Lesson:** Database transactions are not committed until explicitly told. Read operations can't see uncommitted writes!

---

### 3. Deployment != Development

**Challenges:**
- Local PostgreSQL uses `localhost`, Render uses `DATABASE_URL` env var
- Flask debug mode must be disabled in production
- Logs are essential when you can't see stdout

**Solutions:**
```python
# Dynamic database connection
database_url = os.getenv('DATABASE_URL')
if database_url:
    self.conn = psycopg.connect(database_url)  # Production
else:
    conninfo = f"host=localhost dbname=carwatch..."  # Local
    self.conn = psycopg.connect(conninfo)

# Proper logging
logger = setup_logger('carwatch')
logger.info("Scrape started at {datetime.now()}")
```

**Lesson:** Design for both environments from day 1. Use environment variables, feature flags, and comprehensive logging.

---

### 4. Small Iterations Beat Big Rewrites

**Process:**
1. First: Build scraper, test locally
2. Then: Add database integration, verify inserts
3. Then: Add price history tracking
4. Then: Build web UI
5. Finally: Add alerts and deploy

**Lesson:** Each step was independently testable. If I'd tried to build everything at once, debugging would have been a nightmare. Ship small, iterate fast.

---

### 5. User Experience > Feature Count

**Temptation:** Add KSL scraper, Facebook Marketplace, filters for color, transmission type...

**Reality:** 
- Craigslist alone provides enough listings
- Users primarily care about make/model/price/year
- A polished single-source experience beats a buggy multi-source one

**Lesson:** Focus on core use case. Polish beats features. Ship an MVP that works perfectly, then expand.

---

## Scaling & Performance Characteristics

### Current System Capacity

| Metric | Current | Theoretical Max | Bottleneck |
|--------|---------|-----------------|------------|
| **Listings** | 500+ | ~50,000 | Database size (but PG handles this easily) |
| **Daily Scrapes** | 2 pages (48 listings) | 10+ pages (240 listings) | Scrape duration + respect rate limits |
| **Concurrent Users** | 10-50 | 500+ | Render free tier (512MB RAM) |
| **Search Response Time** | <200ms | <100ms with Redis | Database indexes |
| **Price History Records** | ~1000 | Millions | Storage cost |

### Scaling Strategies

**Horizontal Scaling:**
- Add Redis for caching popular searches (1hr TTL)
- Deploy multiple Flask workers (Gunicorn already supports this)
- Use CDN for static assets (Chart.js, CSS)

**Vertical Scaling:**
- Upgrade Render instance (more RAM/CPU)
- Optimize SQL queries (EXPLAIN ANALYZE)
- Add database read replicas for search queries

**Data Partitioning:**
- Archive listings older than 1 year to cold storage
- Shard by city/region if expanding beyond SLC

### Performance Optimizations Implemented

1. **Database Indexes:**
   ```sql
   CREATE INDEX idx_listings_external_id ON listings(external_id);
   CREATE INDEX idx_listings_make_model ON listings(make, model);
   CREATE INDEX idx_price_history_listing_id ON price_history(listing_id);
   ```

2. **Query Optimization:**
   - Pagination with `LIMIT`/`OFFSET` to avoid fetching all results
   - `COUNT(*)` separate from main query (faster)
   - Parameterized queries (SQL injection prevention + query plan caching)

3. **Frontend:**
   - Load Chart.js from CDN (browser caching)
   - Vanilla JS (no React/Vue overhead)
   - Lazy loading of listing details

---

## Security & Authentication

### Current Security Measures

1. **SQL Injection Prevention:**
   - All queries use parameterized statements (psycopg3)
   - No string interpolation of user input

2. **Input Validation:**
   - Email format validation on alerts
   - Numeric type checking for year/price/mileage
   - Whitelist of allowed sort fields

3. **Rate Limiting:**
   - Scraper respects 2-second delays
   - Could add Flask-Limiter for API endpoints

### Authentication (Not Implemented Yet)

**Current:** Alert system uses email but no authentication. Anyone can view/delete any alert if they know the email.

**Future Enhancements:**
- User accounts with JWT tokens
- OAuth2 (Google/Facebook login)
- Email verification for alerts
- CSRF protection for alert creation/deletion
- HTTPS enforcement (Render provides this)

**Trade-off:** Chose to prioritize core functionality over auth for MVP. For a public production app, authentication would be essential.

---

## Concurrency & Failover Strategy

### Concurrency Handling

**Scraper:**
- Single process (no concurrency issues)
- APScheduler ensures jobs don't overlap (misfire grace time: 60s)
- Future: Could parallelize with Celery task queue

**Database:**
- PostgreSQL handles concurrent reads naturally (MVCC)
- `ON CONFLICT DO UPDATE` prevents race conditions on inserts
- Row-level locking for price_history inserts (implicit in transaction)

**Web Server:**
- Gunicorn with 4 workers (each handles requests independently)
- Stateless API (no shared memory between requests)
- Database connection pooling (psycopg3 built-in)

### Failover Strategy

**Database:**
- Render provides automated daily backups
- Manual backups before schema changes
- `pg_dump` for disaster recovery

**Scraper:**
- If scrape fails, APScheduler retries next scheduled run
- Logging to file for post-mortem analysis
- Stale listing detection (7-day grace period)

**Web Server:**
- Render auto-restarts on crash
- Health checks (could add `/health` endpoint)
- Graceful degradation (if DB down, show cached data)

**Future Improvements:**
- Sentry for error tracking
- PagerDuty for alerts on scrape failures
- Read replicas for zero-downtime deployments

---

## Future Enhancements

### Short-Term (Next Iteration)

1. **KSL Cars Scraper**
   - Already have skeleton code in `ksl_scraper.py`
   - Need to handle their anti-bot measures (PerimeterX CAPTCHA)
   - Would double listing count

2. **Price Drop Alerts**
   - Notify users when a specific listing's price drops
   - "Watch this listing" button

3. **Advanced Search**
   - Keyword search in description
   - Seller type filter (dealer vs private)
   - Color, transmission, fuel type

### Long-Term (Dream Features)

1. **Mobile App**
   - React Native or Flutter
   - Push notifications for alerts
   - Save favorite listings

2. **AI-Powered Insights**
   - "This car is priced 15% below market average!"
   - Predict when a car will sell based on price/demand
   - Auto-suggest alert criteria based on user behavior

3. **Multi-City Support**
   - Expand beyond Salt Lake City
   - City selector in UI
   - Regional price comparisons

4. **Market Reports**
   - Weekly email digest of market trends
   - Export data to CSV for analysis
   - Shareable reports with charts

---

## Code Repository Structure

```
carwatch/
├── src/
│   ├── database/
│   │   ├── db.py              # Database abstraction layer
│   │   └── schema.sql          # Table definitions
│   ├── scrapers/
│   │   ├── craigslist_scraper.py   # Main scraper (implemented)
│   │   ├── ksl_scraper.py          # KSL scraper (skeleton)
│   │   ├── scraper_manager.py      # Orchestration & alert checking
│   │   └── job_scheduler.py        # APScheduler configuration
│   ├── web/
│   │   ├── app.py                  # Flask routes
│   │   └── templates/
│   │       ├── base.html
│   │       ├── index.html          # Search page
│   │       ├── listing_detail.html # Price history
│   │       ├── alerts.html         # Alert management
│   │       └── stats.html          # Statistics dashboard
│   └── utils/
│       └── logger.py               # Logging configuration
├── requirements.txt
├── render.yaml                     # Render deployment config
├── README.md                       # Project documentation
├── PROGRESS_LOG.md                 # Time tracking
└── FINAL_REPORT.md                 # This document
```

---

## ⏱Time Investment

Total Hours: **47 hours**

Breakdown:
- Initial design & planning: 4.5 hours
- Database setup & schema: 3.5 hours
- Scraper development: 5.5 hours
- Scheduler & logging: 4 hours
- Web interface: 7 hours
- Listing detail page: 3.5 hours
- Statistics dashboard: 3.5 hours
- Alert system: 7.5 hours
- Deployment & testing: 6 hours
- Documentation: 2 hours

**Most Time-Consuming:** Alert system (email integration, HTML templates, matching logic)  
**Most Satisfying:** Seeing the price history chart populate with real data!

---

## Demo Video

**[Link to Demo Video]** Recording of DEC 10th class last presentation

### Video Contents:
1. **Live scraping demonstration** (run `python -m src.scrapers.job_scheduler --test`)
2. **Search functionality** (filter by make, model, price range)
3. **Price history visualization** (Chart.js line graph)
4. **Alert creation** (set max price, email notification demo)
5. **Statistics dashboard** (market insights)

**Duration:** 5-7 minutes  
**Format:** Screen recording with voiceover

---

## Links

- **GitHub Repository:** https://github.com/caysonhhanson/finalprojectcs462
- **Live Application:** https://finalprojectcs462-1.onrender.com

---

## Submission Information

**Student Permission:**  
 *No* - I do not give permission for this project to be used as an example for future students. 

**Course Feedback:**  
This project was a fantastic learning experience. The open-ended nature allowed me to explore areas I was genuinely interested in (web scraping, data visualization) while also forcing me to learn production deployment. The 40+ hour time investment was challenging but rewarding. I'd recommend requiring students to deploy their projects—debugging remote systems taught me more than any local development could.

---

**Built by Cayson Hanson | Fall 2025**