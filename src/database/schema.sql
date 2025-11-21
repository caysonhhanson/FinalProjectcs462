-- Drop tables if they exist (for development)
DROP TABLE IF EXISTS alert_matches CASCADE;
DROP TABLE IF EXISTS alerts CASCADE;
DROP TABLE IF EXISTS price_history CASCADE;
DROP TABLE IF EXISTS listings CASCADE;

-- Listings table
CREATE TABLE listings (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(255) UNIQUE NOT NULL,
    source VARCHAR(50) NOT NULL,
    url TEXT NOT NULL,
    title TEXT,
    price DECIMAL(10,2),
    year INTEGER,
    make VARCHAR(100),
    model VARCHAR(100),
    mileage INTEGER,
    location VARCHAR(255),
    description TEXT,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Price history table
CREATE TABLE price_history (
    id SERIAL PRIMARY KEY,
    listing_id INTEGER REFERENCES listings(id) ON DELETE CASCADE,
    price DECIMAL(10,2) NOT NULL,
    recorded_at TIMESTAMP DEFAULT NOW()
);

-- Alerts table
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    make VARCHAR(100),
    model VARCHAR(100),
    min_year INTEGER,
    max_year INTEGER,
    max_price DECIMAL(10,2),
    max_mileage INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Alert matches table
CREATE TABLE alert_matches (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER REFERENCES alerts(id) ON DELETE CASCADE,
    listing_id INTEGER REFERENCES listings(id) ON DELETE CASCADE,
    matched_at TIMESTAMP DEFAULT NOW(),
    notified BOOLEAN DEFAULT FALSE
);

-- Create indexes for performance
CREATE INDEX idx_listings_external_id ON listings(external_id);
CREATE INDEX idx_listings_is_active ON listings(is_active);
CREATE INDEX idx_listings_make_model ON listings(make, model);
CREATE INDEX idx_price_history_listing_id ON price_history(listing_id);
CREATE INDEX idx_alerts_active ON alerts(is_active);
