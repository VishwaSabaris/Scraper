import requests
import json
from bs4 import BeautifulSoup

url = "https://www.naukri.com/data-analyst-jobs-in-bangalore"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

r = requests.get(url, headers=headers, timeout=15)
print(f"Status: {r.status_code}")

soup = BeautifulSoup(r.text, 'html.parser')
next_data = soup.find('script', id='__NEXT_DATA__')

with open("scratch/naukri_page.html", "w", encoding="utf-8") as f:
    f.write(r.text)
print("Saved raw HTML to scratch/naukri_page.html")

# Look for self.__next_f or JSON objects containing filter information
for idx, s in enumerate(soup.find_all('script')):
    txt = s.string or ""
    if "wfhType" in txt or "ctcFilter" in txt or "Engineering - Software" in txt or "Work mode" in txt:
        print(f"Script #{idx} matched filter keywords, length {len(txt)}")
        with open(f"scratch/script_{idx}.js", "w", encoding="utf-8") as f:
            f.write(txt)

