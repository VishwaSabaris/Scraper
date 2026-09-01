import asyncio
import os
import sys
sys.path.append(os.path.abspath("."))
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS

async def inspect_cards():
    user_dir = os.path.abspath("./ziprecruiter_session")
    os.makedirs(user_dir, exist_ok=True)
    
    url = "https://www.ziprecruiter.com/jobs-search?search=software+developer&location=London"
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=True,
            args=CHROMIUM_STEALTH_ARGS,
            viewport={'width': 1366, 'height': 768}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        print(f"Navigating to: {url}")
        await page.goto(url, timeout=30000)
        await asyncio.sleep(4)
        
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        articles = soup.find_all("article")
        print(f"Total <article> elements: {len(articles)}")
        
        for idx, art in enumerate(articles[:5]):
            print(f"\n--- Article {idx + 1} ---")
            # Print classes & id
            print("Classes:", art.get("class"))
            print("ID:", art.get("id"))
            
            # Title
            h2 = art.find(["h2", "h3", "h1"])
            title = h2.get_text(strip=True) if h2 else "No title heading"
            print("Title:", title)
            
            # Link
            link = art.find("a", href=True)
            href = link.get("href") if link else "No link"
            print("Href:", href)
            
            # Company & Location
            company_el = art.find(attrs={"data-testid": "job-card-company"}) or art.find(class_=lambda c: c and "company" in c)
            location_el = art.find(attrs={"data-testid": "job-card-location"}) or art.find(class_=lambda c: c and "location" in c)
            print("Company:", company_el.get_text(strip=True) if company_el else "None")
            print("Location:", location_el.get_text(strip=True) if location_el else "None")
            
            # Date posted
            time_el = art.find("time") or art.find(class_=lambda c: c and ("date" in c or "time" in c or "ago" in c))
            print("Date/Time:", time_el.get_text(strip=True) if time_el else "None")
            
            # Snippet text
            snippet = art.get_text(separator=' ', strip=True)[:150]
            print("Snippet:", snippet)
            
        await context.close()

if __name__ == "__main__":
    asyncio.run(inspect_cards())
