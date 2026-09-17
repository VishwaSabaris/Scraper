import asyncio
import os
import sys
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import CHROMIUM_STEALTH_ARGS

async def search_google_site(site_domain, query_terms, location=""):
    q = f'site:{site_domain} "{query_terms}"'
    if location and location.lower() not in ["any", "all", "worldwide", "remote"]:
        q += f' "{location}"'
        
    google_url = f"https://www.google.com/search?q={urllib.parse.quote(q)}"
    print(f"[*] Google Search URL: {google_url}")
    
    user_dir = os.path.abspath("./google_search_session")
    os.makedirs(user_dir, exist_ok=True)
    
    jobs = []
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=True,
            args=CHROMIUM_STEALTH_ARGS,
            viewport={'width': 1366, 'height': 768}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        try:
            await page.goto(google_url, timeout=30000)
            await asyncio.sleep(3)
            print('Page Title:', await page.title(), 'URL:', page.url)
            
            # Dismiss consent if present
            consent_btn = page.locator("button:has-text('Accept all'), button:has-text('I agree'), div:has-text('Accept all')")
            if await consent_btn.count() > 0:
                try:
                    await consent_btn.first.click()
                    await asyncio.sleep(2)
                except Exception:
                    pass
                    
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            links = soup.find_all('a', href=True)
            for a in links:
                href = a['href']
                h3 = a.find('h3')
                if not h3:
                    continue
                title = h3.text.strip()
                if site_domain not in href:
                    continue
                    
                # Clean Google URL
                clean_href = href
                if '/url?' in href:
                    parsed = urllib.parse.urlparse(href)
                    qs = urllib.parse.parse_qs(parsed.query)
                    clean_href = qs.get('q', [href])[0]
                    
                clean_href = clean_href.split('&')[0].split('#')[0]
                
                # Check snippet
                parent = a.find_parent('div')
                snippet = ""
                if parent:
                    snippet = parent.get_text(separator=" ", strip=True)
                    
                jobs.append({
                    "title": title,
                    "url": clean_href,
                    "snippet": snippet
                })
        finally:
            await context.close()
            
    return jobs

async def main():
    print("\n--- Testing Google site: search for Careerjet ---")
    cj_jobs = await search_google_site("careerjet.co.in/job", "Lead Generation Executive", "India")
    print(f"[+] Found {len(cj_jobs)} Careerjet jobs:")
    for j in cj_jobs[:5]:
        print("  - Title:", j['title'])
        print("    URL  :", j['url'])
        
    print("\n--- Testing Google site: search for Jobspresso ---")
    jp_jobs = await search_google_site("jobspresso.co", "Sales")
    print(f"[+] Found {len(jp_jobs)} Jobspresso jobs:")
    for j in jp_jobs[:5]:
        print("  - Title:", j['title'])
        print("    URL  :", j['url'])

if __name__ == "__main__":
    asyncio.run(main())
