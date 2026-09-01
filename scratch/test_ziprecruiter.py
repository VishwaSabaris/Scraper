import asyncio
import os
import sys
sys.path.append(os.path.abspath("."))
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS

async def test_zip_urls():
    user_dir = os.path.abspath("./ziprecruiter_session")
    os.makedirs(user_dir, exist_ok=True)
    
    urls = [
        "https://www.ziprecruiter.com/jobs-search?search=software+developer&location=London",
        "https://www.ziprecruiter.com/jobs-search?search=software+developer&location=United+Kingdom",
        "https://www.ziprecruiter.co.uk/jobs-search?search=Software%20Developer&location=London",
        "https://www.ziprecruiter.com/jobs-search?search=software+developer&location=London%2C+UK"
    ]
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=False,
            channel="chrome",
            args=CHROMIUM_STEALTH_ARGS,
            viewport={'width': 1366, 'height': 768}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        for url in urls:
            print(f"\n==========================================")
            print(f"Navigating to: {url}")
            try:
                resp = await page.goto(url, timeout=30000)
                print(f"Status: {resp.status if resp else 'None'}")
                print(f"Final URL: {page.url}")
                print(f"Title: {await page.title()}")
                
                await asyncio.sleep(5)
                
                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")
                
                # Check for various card selectors
                articles = soup.find_all("article")
                print(f"Articles count (<article>): {len(articles)}")
                
                divs_job = soup.find_all(class_=lambda c: c and ("job" in c or "card" in c or "result" in c))
                print(f"Divs matching job/card/result: {len(divs_job)}")
                
                # Search for specific data-testid or class elements
                testids = [tag.get("data-testid") for tag in soup.find_all(attrs={"data-testid": True})]
                job_testids = [t for t in testids if "job" in t]
                print(f"Job related data-testids found: {set(job_testids[:10])}")
                
                # Look for headings (h2, h3) with job links
                h2s = soup.find_all(["h2", "h3"])
                print(f"Headings count: {len(h2s)}")
                for h in h2s[:5]:
                    print("  Heading:", h.get_text(strip=True)[:60])
                    
                # Inspect links containing /job/ or /jobs/ or lk=
                job_links = soup.find_all("a", href=lambda h: h and ("/job/" in h or "/jobs/" in h or "lk=" in h or "job_result" in h))
                print(f"Job links found: {len(job_links)}")
                for l in job_links[:5]:
                    print("  Job link:", l.get("href"), "| Text:", l.get_text(strip=True)[:40])
                    
            except Exception as e:
                print(f"Error on {url}: {e}")
                
        await context.close()

if __name__ == "__main__":
    asyncio.run(test_zip_urls())
