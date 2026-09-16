import asyncio
import os
import sys
import json
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context

async def test_cb_render():
    user_dir = os.path.abspath("./careerbuilder_session_run")
    os.makedirs(user_dir, exist_ok=True)
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=True,
            args=CHROMIUM_STEALTH_ARGS,
            viewport={'width': 1366, 'height': 768}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        captured_api = []
        async def handle_response(response):
            if "careerbuilder.com" in response.url and ("json" in response.headers.get("content-type", "") or "graphql" in response.url):
                try:
                    data = await response.json()
                    captured_api.append({"url": response.url, "data": data})
                except Exception:
                    pass
                    
        page.on("response", handle_response)
        
        u = "https://www.careerbuilder.com/job-listings/search?q=Sales+Development+Representative&where=USA"
        print("Navigating to:", u)
        await page.goto(u, timeout=40000, wait_until="domcontentloaded")
        
        # Wait up to 15 seconds for skeleton cards to be replaced by actual cards
        for sec in range(15):
            await asyncio.sleep(1)
            skels = await page.locator("div[class*='SkeletonJobCardWrap']").count()
            cards = await page.locator("article, div[data-testid='JobCard'], a[href*='/job/'], a[href*='/job-listings/']").count()
            print(f"Sec {sec+1}: skeletons={skels}, real card elements={cards}")
            if cards > 2 and skels == 0:
                print("Render complete!")
                break
                
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        # Check all links
        job_links = soup.find_all("a", href=lambda h: h and ("/job/" in h or "/job-listings/" in h or "/jobs/" in h))
        print("Found job links:", len(job_links))
        for jl in job_links[:5]:
            print("  Link:", jl.get_text(strip=True), "->", jl.get("href"))
            
        print("Captured API responses:", len(captured_api))
        for api in captured_api:
            print("  API URL:", api["url"][:100])
            
        await context.close()

if __name__ == "__main__":
    asyncio.run(test_cb_render())
