import urllib.parse
import json
import requests
from bs4 import BeautifulSoup

def test_engines():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    
    # 1. DuckDuckGo HTML
    ddg_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote('site:careerbuilder.com Sales Development Representative')}"
    r = requests.get(ddg_url, headers=headers, timeout=10)
    print("DDG status:", r.status_code)
    soup = BeautifulSoup(r.text, 'html.parser')
    links = [a.get('href') for a in soup.find_all('a', class_='result__url')]
    print("DDG links:", len(links), links[:3])
    
    # 2. Careerbuilder API check
    # Check if careerbuilder has public api
    cb_api = "https://www.careerbuilder.com/api/jobs"
    try:
        r2 = requests.get(cb_api, params={"keywords": "Sales Development Representative"}, headers=headers, timeout=10)
        print("CB API status:", r2.status_code)
    except Exception as e:
        print("CB API error:", e)

if __name__ == "__main__":
    test_engines()
