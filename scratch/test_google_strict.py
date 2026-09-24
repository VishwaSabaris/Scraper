import asyncio
import os
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import sys
sys.path.insert(0, '.')
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from utils import CHROMIUM_STEALTH_ARGS

async def test_google_wf():
    query = 'site:wellfound.com/jobs "Lead Generation" India'
    user_dir = os.path.abspath("./wellfound_direct_session")
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=False,
            channel="chrome",
            args=CHROMIUM_STEALTH_ARGS,
            viewport={'width': 1366, 'height': 768}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        google_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        print(f"Navigating to {google_url}...")
        await page.goto(google_url, wait_until="domcontentloaded", timeout=25000)
        await asyncio.sleep(2)
        
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        found = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            decoded = urllib.parse.unquote(href)
            actual_url = decoded
            if '/url?' in decoded:
                parsed = urllib.parse.urlparse(decoded)
                qs = urllib.parse.parse_qs(parsed.query)
                target = qs.get('q') or qs.get('url')
                if target:
                    actual_url = target[0]
            clean = actual_url.split('#')[0].split('?')[0]
            if 'wellfound.com/jobs/' in clean:
                found.append(clean)
                
        print(f"Found {len(found)} Wellfound jobs from Google:")
        for f in set(found):
            print(" ", f)
            
        await context.close()

if __name__ == "__main__":
    asyncio.run(test_google_wf())
