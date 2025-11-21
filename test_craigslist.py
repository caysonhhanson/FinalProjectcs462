import requests
from bs4 import BeautifulSoup

url = "https://saltlakecity.craigslist.org/search/cta"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

print("Fetching Craigslist page...")
response = requests.get(url, headers=headers)
print(f"Status code: {response.status_code}")

soup = BeautifulSoup(response.text, 'html.parser')

# Look for different possible listing containers
print("\nLooking for listings...")
print(f"1. cl-static-search-result: {len(soup.find_all('li', class_='cl-static-search-result'))}")
print(f"2. result-row: {len(soup.find_all('li', class_='result-row'))}")
print(f"3. cl-search-result: {len(soup.find_all('li', class_='cl-search-result'))}")
print(f"4. Any <li> with 'result' in class: {len(soup.find_all('li', class_=lambda x: x and 'result' in x.lower() if x else False))}")

# Print first listing HTML to see structure
print("\nFirst listing HTML (if found):")
first_result = soup.find('li', class_=lambda x: x and 'result' in x.lower() if x else False)
if first_result:
    print(first_result.prettify()[:500])
else:
    print("No listings found. Page may have changed.")
    print("\nSaving HTML to check manually...")
    with open('craigslist_page.html', 'w') as f:
        f.write(response.text)
    print("Saved to craigslist_page.html - you can open this in a browser")
