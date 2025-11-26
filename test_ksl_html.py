# test_ksl_html.py
import requests
from bs4 import BeautifulSoup

url = "https://cars.ksl.com/search/newused"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

print("Fetching KSL page...")
response = requests.get(url, headers=headers)
print(f"Status code: {response.status_code}\n")

soup = BeautifulSoup(response.text, 'html.parser')

# Try different possible selectors
print("Looking for listings with different selectors:\n")
print(f"1. class='listing-item': {len(soup.find_all(class_='listing-item'))}")
print(f"2. class='listing': {len(soup.find_all(class_='listing'))}")
print(f"3. data-role='listing': {len(soup.find_all(attrs={'data-role': 'listing'}))}")
print(f"4. article tags: {len(soup.find_all('article'))}")
print(f"5. class contains 'item': {len(soup.find_all(class_=lambda x: x and 'item' in x.lower() if x else False))}")

# Print first few divs to see structure
print("\n" + "="*80)
print("First few main content divs:")
print("="*80)

# Save HTML to file for inspection
with open('ksl_page.html', 'w', encoding='utf-8') as f:
    f.write(response.text)
print("\n✅ Saved full HTML to ksl_page.html")

# Look for links that might be listings
links = soup.find_all('a', href=True)
listing_links = [link for link in links if '/listing/' in link['href'] or 'detail' in link['href'].lower()]
print(f"\n🔗 Found {len(listing_links)} links that might be listings")
if listing_links:
    print("\nSample listing URLs:")
    for link in listing_links[:5]:
        print(f"  - {link['href']}")