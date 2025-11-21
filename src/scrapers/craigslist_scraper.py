import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime

class CraigslistScraper:
    def __init__(self, city="saltlakecity"):
        self.city = city
        self.base_url = f"https://{city}.craigslist.org/search/cta"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_listings(self, max_pages=2):
        """Scrape car listings from Craigslist"""
        all_listings = []
        
        for page in range(max_pages):
            print(f"📄 Scraping page {page + 1}...")
            
            # Craigslist pagination: ?s=0, ?s=120, ?s=240, etc.
            params = {'s': page * 120}
            
            try:
                response = requests.get(
                    self.base_url,
                    headers=self.headers,
                    params=params,
                    timeout=10
                )
                response.raise_for_status()
                
                listings = self._parse_page(response.text)
                all_listings.extend(listings)
                
                print(f"  ✅ Found {len(listings)} listings on page {page + 1}")
                
                # Be respectful - don't hammer the server
                time.sleep(2)
                
            except Exception as e:
                print(f"  ❌ Error scraping page {page + 1}: {e}")
                continue
        
        print(f"\n🎉 Total listings scraped: {len(all_listings)}")
        return all_listings
    
    def _parse_page(self, html):
        """Parse a Craigslist search results page"""
        soup = BeautifulSoup(html, 'html.parser')
        listings = []
        
        # Find all listing cards
        results = soup.find_all('li', class_='cl-static-search-result')
        
        for result in results:
            try:
                listing = self._parse_listing(result)
                if listing:
                    listings.append(listing)
            except Exception as e:
                print(f"    ⚠️ Error parsing listing: {e}")
                continue
        
        return listings
    
    def _parse_listing(self, result):
        """Parse a single listing"""
        # Get the link - it's the direct child <a> tag
        link = result.find('a')
        if not link:
            return None
        
        url = link.get('href')
        if not url:
            return None
            
        if not url.startswith('http'):
            url = f"https://{self.city}.craigslist.org{url}"
        
        # Extract listing ID from URL
        external_id = self._extract_id_from_url(url)
        
        # Get title
        title_elem = result.find('div', class_='title')
        title = title_elem.get_text(strip=True) if title_elem else "No title"
        
        # Get price
        price_elem = result.find('div', class_='price')
        price = self._parse_price(price_elem.get_text(strip=True) if price_elem else "")
        
        # Get location
        location_elem = result.find('div', class_='location')
        location = location_elem.get_text(strip=True) if location_elem else ""
        
        # Get details div for any meta info
        details_elem = result.find('div', class_='details')
        meta_text = details_elem.get_text(strip=True) if details_elem else ""
        
        # Parse year, make, model from title
        year, make, model = self._parse_title(title)
        
        # Parse mileage from meta or title
        mileage = self._parse_mileage(meta_text + " " + title)
        
        listing = {
            'external_id': external_id,
            'source': 'craigslist',
            'url': url,
            'title': title,
            'price': price,
            'year': year,
            'make': make,
            'model': model,
            'mileage': mileage,
            'location': location,
            'description': meta_text
        }
        
        return listing
    
    def _extract_id_from_url(self, url):
        """Extract listing ID from URL"""
        # URL format: https://saltlakecity.craigslist.org/cto/d/title/1234567890.html
        match = re.search(r'/(\d+)\.html', url)
        if match:
            return f"cl_{match.group(1)}"
        return f"cl_{hash(url)}"
    
    def _parse_price(self, price_text):
        """Extract numeric price from text like '$15,500'"""
        if not price_text:
            return None
        
        # Remove $ and commas, extract number
        match = re.search(r'\$?([\d,]+)', price_text)
        if match:
            return float(match.group(1).replace(',', ''))
        return None
    
    def _parse_title(self, title):
        """Extract year, make, model from title"""
        # Common pattern: "2018 Honda Civic LX"
        year = None
        make = None
        model = None
        
        # Extract year (4 digits)
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', title)
        if year_match:
            year = int(year_match.group(1))
        
        # Common car makes
        makes = ['honda', 'toyota', 'ford', 'chevrolet', 'chevy', 'nissan', 
                 'mazda', 'subaru', 'hyundai', 'kia', 'volkswagen', 'vw',
                 'bmw', 'mercedes', 'audi', 'lexus', 'acura', 'infiniti',
                 'dodge', 'jeep', 'ram', 'gmc', 'buick', 'cadillac']
        
        title_lower = title.lower()
        for car_make in makes:
            if car_make in title_lower:
                make = car_make.title()
                # Try to extract model (word after make)
                pattern = rf'{car_make}\s+(\w+)'
                model_match = re.search(pattern, title_lower)
                if model_match:
                    model = model_match.group(1).title()
                break
        
        return year, make, model
    
    def _parse_mileage(self, text):
        """Extract mileage from text"""
        # Look for patterns like "65000 miles" or "65k"
        match = re.search(r'([\d,]+)k?\s*(miles?|mi)', text.lower())
        if match:
            mileage_str = match.group(1).replace(',', '')
            mileage = float(mileage_str)
            # If it says "65k", multiply by 1000
            if 'k' in match.group(0).lower():
                mileage *= 1000
            return int(mileage)
        return None


# Test the scraper
if __name__ == "__main__":
    print("🚗 Starting Craigslist Scraper Test...\n")
    
    scraper = CraigslistScraper(city="saltlakecity")
    listings = scraper.scrape_listings(max_pages=1)
    
    print(f"\n📊 Sample Listings:")
    print("=" * 80)
    
    for i, listing in enumerate(listings[:5], 1):
        print(f"\n{i}. {listing['title']}")
        print(f"   Price: ${listing['price']:,.2f}" if listing['price'] else "   Price: N/A")
        print(f"   Year: {listing['year']}, Make: {listing['make']}, Model: {listing['model']}")
        print(f"   Mileage: {listing['mileage']:,}" if listing['mileage'] else "   Mileage: N/A")
        print(f"   Location: {listing['location']}")
        print(f"   URL: {listing['url'][:60]}...")
