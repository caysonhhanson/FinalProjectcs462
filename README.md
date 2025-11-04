# FinalProjectcs462

# Initial Design Document

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CarWatch System                          │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────┐
│      KSL Cars    │         │Facebook Marketplace│
│   (HTML Pages)   │         │   (HTML Pages)    │
└────────┬─────────┘         └────────┬──────────┘
         │                            │
         │ HTTP Requests              │ HTTP Requests
         ▼                            ▼
┌─────────────────────────────────────────────────┐
│         Web Scraper (Python)                     │
│  - BeautifulSoup4/Scrapy                        │
│  - Runs every 24 hours (APScheduler)            │
│  - Extracts: price, title, year, make, model    │
└────────────────────┬────────────────────────────┘
                     │
                     │ INSERT/UPDATE
                     ▼
┌─────────────────────────────────────────────────┐
│         PostgreSQL Database                      │
│                                                  │
│  Tables:                                         │
│  - listings (current state)                     │
│  - price_history (time-series)                  │
│  - alerts (user preferences)                    │
│  - alert_matches (notifications log)            │
└────────────────────┬────────────────────────────┘
                     │
                     │ SELECT queries
                     ▼
┌─────────────────────────────────────────────────┐
│       Flask/FastAPI Web Application             │
│                                                  │
│  Endpoints:                                      │
│  - GET /listings (search & filter)              │
│  - GET /listing/:id (details + history)         │
│  - POST /alerts (create alert)                  │
│  - GET /alerts (user's alerts)                  │
└────────────────────┬────────────────────────────┘
                     │
                     │ HTTP Response
                     ▼
┌─────────────────────────────────────────────────┐
│          Web Frontend (HTML/JS)                 │
│                                                  │
│  Pages:                                          │
│  - Search/Browse listings                       │
│  - Listing detail with price chart              │
│  - Create/manage alerts                         │
└─────────────────────────────────────────────────┘

         ┌──────────────────────┐
         │  Alert Notification  │
         │  System (Email)      │
         │  - Checks daily      │
         │  - Matches alerts    │
         └──────────────────────┘
```

## Database Schema (ERD)

```
┌─────────────────────────────────────┐
│           LISTINGS                  │
├─────────────────────────────────────┤
│ PK  id                 SERIAL       │
│     external_id        VARCHAR(255) │ UNIQUE
│     source             VARCHAR(50)  │
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
│     is_active          BOOLEAN      │
│     created_at         TIMESTAMP    │
│     updated_at         TIMESTAMP    │
└──────────┬──────────────────────────┘
           │
           │ 1:N
           │
           ▼
┌─────────────────────────────────────┐
│         PRICE_HISTORY               │
├─────────────────────────────────────┤
│ PK  id                 SERIAL       │
│ FK  listing_id         INTEGER      │───┐
│     price              DECIMAL      │   │
│     recorded_at        TIMESTAMP    │   │
└─────────────────────────────────────┘   │
                                          │
           ┌──────────────────────────────┘
           │
           │
┌──────────▼──────────────────────────┐
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
           │
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
```

## Key Data Flows

**1. Scraping Flow (Writes)**
```
Every 24 hours:
1. Scraper fetches pages from Craigslist/Facebook
2. Parses HTML to extract listing data
3. For each listing:
   - Check if external_id exists in database
   - If NEW: INSERT into listings table
   - If EXISTS: 
     - Compare current price to stored price
     - If different: INSERT into price_history
     - UPDATE last_seen timestamp
4. Mark listings not seen in 7 days as is_active=false
```

**2. Alert Matching Flow (Reads + Writes)**
```
Daily (after scraping):
1. Get all active alerts from database
2. For each alert:
   - Query new listings matching criteria
   - For matches: INSERT into alert_matches
3. Send email notifications for unnotified matches
4. Mark as notified
```

**3. User Search Flow (Reads)**
```
User visits website:
1. User enters search criteria (make, model, price range)
2. Query listings table with filters
3. Return results ordered by most recent
4. User clicks listing → fetch price_history
5. Display price trend chart
```

## Scaling Characteristics

| Component | Expected Load | Scaling Strategy |
|-----------|---------------|------------------|
| **Scraper** | 1000-5000 listings/day | Single-threaded initially. Can add multiple workers with task queue (Celery) |
| **Database Writes** | ~50-200 writes/hour (during scrape) | PostgreSQL handles this easily. Add indexes on commonly queried fields |
| **Database Reads** | ~100-500 reads/hour (user searches) | Add Redis cache for popular searches (1hr TTL). Postgres can handle 1000s/sec |
| **Web Server** | 10-50 concurrent users initially | Flask + Gunicorn handles this. Scale horizontally if needed |

## Concurrency Considerations

**Scraper Concurrency:**
- Initially: Single scraper process (no conflicts)
- Future: Use row-level locking or upsert operations if multiple scrapers

**Database Concurrency:**
- PostgreSQL handles concurrent reads naturally
- Use transactions for price_history inserts
- Proper indexes to prevent lock contention

**User Sessions:**
- Stateless API design (no session issues)
- Read-heavy workload (minimal lock contention)

## Performance Characteristics

**Expected Response Times:**
- Search listings: < 200ms (with indexes)
- View listing detail: < 100ms
- Price history query: < 150ms
- Alert creation: < 50ms

**Storage Estimates:**
- ~500 bytes per listing
- 5000 listings = 2.5MB
- 100 price changes/day = 50KB/day = 18MB/year
- Very manageable for PostgreSQL

## Security Considerations

**Phase 1 (MVP):**
- Input validation on all user inputs
- Parameterized SQL queries (prevent SQL injection)
- Rate limiting on API endpoints

**Phase 2 (if time):**
- User authentication (JWT tokens)
- Email verification for alerts
- HTTPS only

## Sample UI Mockup (Rough Sketch)

```
┌─────────────────────────────────────────────────┐
│  CarWatch                         [Login/Signup]│
├─────────────────────────────────────────────────┤
│                                                  │
│  Search Cars:                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │Make:  [▼]│ │Model: [▼]│ │Max Price:│       │
│  └──────────┘ └──────────┘ └──────────┘       │
│  [Search Button]  [Create Alert]               │
│                                                  │
│  Results: 47 cars found                         │
│  ┌────────────────────────────────────────────┐│
│  │ 2018 Honda Civic          $15,500  ↓ $500  ││
│  │ 65k miles • Salt Lake City                 ││
│  │ First seen: 2 days ago                     ││
│  └────────────────────────────────────────────┘│
│  ┌────────────────────────────────────────────┐│
│  │ 2019 Toyota Corolla       $17,200          ││
│  │ 42k miles • Provo                          ││
│  │ First seen: 5 hours ago  NEW!             ││
│  └────────────────────────────────────────────┘│
│                                                  │
└─────────────────────────────────────────────────┘

Listing Detail Page:
┌─────────────────────────────────────────────────┐
│  2018 Honda Civic LX                            │
│  Current Price: $15,500                         │
│                                                  │
│  Price History:                                 │
│  $16,500 │     ●                                │
│  $16,000 │                                      │
│  $15,500 │                    ●                 │
│  $15,000 │                                      │
│          └─────────────────────────────         │
│           Nov 1    Nov 15   Dec 1              │
│                                                  │
│  Details:                                       │
│  • Year: 2018                                   │
│  • Mileage: 65,000                             │
│  • Location: Salt Lake City                    │
│                                                  │
│  [View Original Listing]  [Set Alert]          │
└─────────────────────────────────────────────────┘
```

## Daily Goals Timeline

**Nov 4-5 (Today/Tomorrow):**
- ✅ Complete Initial Pitch Report
- ✅ Complete Initial Design Document
- Create GitHub repo with README
- Initialize Python project structure
- Set up PostgreSQL locally

**Nov 6-7:**
- Build basic Craigslist scraper
- Create database schema
- Test inserting scraped data

**Nov 8-10:**
- Add price history tracking logic
- Implement scraper scheduler
- Add error handling & logging

**Nov 11-13:**
- Add Facebook Marketplace scraper
- Handle duplicate detection
- Mark inactive listings

**Nov 14-17:**
- Build Flask API with basic endpoints
- Create simple HTML frontend
- Implement search/filter functionality

**Nov 18-20:**
- Add price history chart visualization
- Improve UI/UX
- Add listing detail page

**Nov 21-24:**
- Implement alert system
- Set up email notifications
- Test alert matching logic

**Nov 25-27:**
- Deploy to Heroku/AWS
- End-to-end testing
- Bug fixes

**Nov 28-Dec 1:**
- Final polish & documentation
- Create demo video
- Prepare presentation slides

**Dec 2-8:**
- In-class presentation
- Submit final report
- Gather feedback

## Success Metrics

By the end of this project, I will have:
- [ ] A working scraper that collects 100+ listings daily
- [ ] A database with price history for at least 500 listings
- [ ] A functional web interface for searching cars
- [ ] An alert system that sends email notifications
- [ ] Deployed application accessible via public URL
- [ ] 30-40 hours of logged development time
- [ ] Complete documentation and demo video
