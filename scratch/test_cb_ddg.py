import urllib.parse
import re
import requests
from bs4 import BeautifulSoup
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import is_role_match

def scrape_careerbuilder_ddg(role="Sales Development Representative", location=""):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    query = f"site:careerbuilder.com {role}"
    if location:
        query += f" {location}"
        
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    print("Fetching DDG URL:", url)
    r = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    results = soup.find_all('div', class_='result')
    print(f"Found {len(results)} search results.")
    
    jobs_data = []
    seen_links = set()
    
    for res in results:
        title_tag = res.find('a', class_='result__snippet') or res.find('a', class_='result__a')
        link_tag = res.find('a', class_='result__url') or res.find('a', class_='result__a')
        snippet_tag = res.find('a', class_='result__snippet')
        
        if not link_tag:
            continue
            
        href = link_tag.get('href', '')
        if 'uddg=' in href:
            match = re.search(r'uddg=([^&]+)', href)
            if match:
                href = urllib.parse.unquote(match.group(1))
                
        if 'careerbuilder.com' not in href:
            continue
            
        clean_href = href.split('?')[0]
        if clean_href in seen_links:
            continue
            
        raw_title = link_tag.get_text(strip=True) if link_tag else ""
        if not raw_title and title_tag:
            raw_title = title_tag.get_text(strip=True)
            
        # Get title from result__a
        a_title = res.find('a', class_='result__a')
        if a_title:
            raw_title = a_title.get_text(strip=True)
            
        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
        
        # Determine company name
        company = "CareerBuilder Employer"
        title = raw_title
        if " - " in raw_title:
            parts = raw_title.split(" - ")
            title = parts[0].strip()
            if len(parts) > 1:
                company = parts[1].replace("CareerBuilder.com", "").replace("CareerBuilder", "").strip()
        elif " | " in raw_title:
            parts = raw_title.split(" | ")
            title = parts[0].strip()
            if len(parts) > 1:
                company = parts[1].replace("CareerBuilder.com", "").replace("CareerBuilder", "").strip()
                
        title = title.replace("Jobs in ", "").replace("Jobs at ", "")
        
        seen_links.add(clean_href)
        jobs_data.append({
            "Job Role": title,
            "Company Name": company or "CareerBuilder Employer",
            "Location": location or "USA / Remote",
            "Date Posted": "2026-09-12",
            "Apply Link": clean_href,
            "Company Link": "N/A",
            "No. of Applicants": "N/A",
            "Company / Job Details": snippet[:350] if snippet else f"Role: {title} | Location: {location or 'Remote'}",
            "Source": "CareerBuilder"
        })
        
    return jobs_data

if __name__ == "__main__":
    jobs = scrape_careerbuilder_ddg("Sales Development Representative", "Bangalore")
    print(f"Extracted {len(jobs)} CareerBuilder jobs!")
    for j in jobs[:3]:
        print(" ", j["Job Role"], "|", j["Company Name"], "|", j["Apply Link"])
