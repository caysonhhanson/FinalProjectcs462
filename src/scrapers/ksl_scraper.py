import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime

class KSLScraper:
    def __init__(self):
        self.base_url = "https://cars.ksl.com/search/newused"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_listings(self, max_pages=2):
        """Scrape car listings from KSL Cars"""
        all_listings = []
        
        for page in range(1, max_pages + 1):
            print(f"🔍 Scraping KSL page {page}...")
            
            params = {
                'page': page,
                'perPage': 24  # KSL default
            }
            
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
                
                print(f"  ✅ Found {len(listings)} listings on page {page}")
                
                # Be respectful
                time.sleep(2)
                
            except Exception as e:
                print(f"  ❌ Error scraping KSL page {page}: {e}")
                continue
        
        print(f"\n🎉 Total KSL listings scraped: {len(all_listings)}")
        return all_listings
    
    def _parse_page(self, html):
        """Parse a KSL search results page"""
        soup = BeautifulSoup(html, 'html.parser')
        listings = []
        
        # KSL uses <div class="listing-item"> or similar
        # You'll need to inspect the actual HTML structure
        results = soup.find_all('div', class_='listing-item')
        
        # If that doesn't work, try these alternatives:
        if not results:
            results = soup.find_all('article', class_='listing')
        if not results:
            results = soup.find_all('div', {'data-role': 'listing'})
        
        for result in results:
            try:
                listing = self._parse_listing(result)
                if listing:
                    listings.append(listing)
            except Exception as e:
                print(f"    ⚠️ Error parsing KSL listing: {e}")
                continue
        
        return listings
    
    def _parse_listing(self, result):
        """Parse a single KSL listing"""
        # Find the link
        link = result.find('a', href=True)
        if not link:
            return None
        
        url = link['href']
        if not url.startswith('http'):
            url = f"https://cars.ksl.com{url}"
        
        # Extract listing ID from URL
        # KSL URLs: https://cars.ksl.com/listing/1234567
        external_id = self._extract_id_from_url(url)
        
        # Get title - usually in <h3> or <h4>
        title_elem = result.find(['h3', 'h4', 'h2'])
        title = title_elem.get_text(strip=True) if title_elem else "No title"
        
        # Get price - usually has class 'price' or data-role='price'
        price_elem = result.find(['div', 'span'], class_=lambda x: x and 'price' in x.lower() if x else False)
        if not price_elem:
            price_elem = result.find(['div', 'span'], attrs={'data-role': 'price'})
        
        price = self._parse_price(price_elem.get_text(strip=True) if price_elem else "")
        
        # Get mileage - usually labeled
        mileage_elem = result.find(text=re.compile(r'\d+,?\d*\s*(miles?|mi)', re.I))
        mileage = self._parse_mileage(mileage_elem) if mileage_elem else None
        
        # Get location
        location_elem = result.find(['div', 'span'], class_=lambda x: x and 'location' in x.lower() if x else False)
        location = location_elem.get_text(strip=True) if location_elem else ""
        
        # Parse year, make, model from title
        year, make, model = self._parse_title(title)
        
        listing = {
            'external_id': external_id,
            'source': 'ksl',
            'url': url,
            'title': title,
            'price': price,
            'year': year,
            'make': make,
            'model': model,
            'mileage': mileage,
            'location': location,
            'description': title  # KSL search page doesn't have full description
        }
        
        return listing
    
    def _extract_id_from_url(self, url):
        """Extract listing ID from URL"""
        # KSL: https://cars.ksl.com/listing/1234567
        match = re.search(r'/listing/(\d+)', url)
        if match:
            return f"ksl_{match.group(1)}"
        return f"ksl_{hash(url)}"
    
    def _parse_price(self, price_text):
        """Extract numeric price from text"""
        if not price_text:
            return None
        
        # Remove $, commas, extract number
        match = re.search(r'\$?([\d,]+)', price_text)
        if match:
            return float(match.group(1).replace(',', ''))
        return None
    
    def _parse_title(self, title):
        """Extract year, make, model from title"""
        year = None
        make = None
        model = None
        
        # Extract year
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', title)
        if year_match:
            year = int(year_match.group(1))
        
        # Common car makes
        makes = ['honda', 'toyota', 'ford', 'chevrolet', 'chevy', 'nissan', 
                 'mazda', 'subaru', 'hyundai', 'kia', 'volkswagen', 'vw',
                 'bmw', 'mercedes', 'audi', 'lexus', 'acura', 'infiniti',
                 'dodge', 'jeep', 'ram', 'gmc', 'buick', 'cadillac', 
                 'tesla', 'porsche', 'volvo', 'mitsubishi']
        
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
        if not text:
            return None
        
        match = re.search(r'([\d,]+)k?\s*(miles?|mi)', str(text).lower())
        if match:
            mileage_str = match.group(1).replace(',', '')
            mileage = float(mileage_str)
            if 'k' in match.group(0).lower():
                mileage *= 1000
            return int(mileage)
        return None


# Test the scraper
if __name__ == "__main__":
    print("🚗 Starting KSL Scraper Test...\n")
    
    scraper = KSLScraper()
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