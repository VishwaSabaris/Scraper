import asyncio
import os
import sys
sys.path.append(os.path.abspath("."))

from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, STEALTH_JS_INIT

async def inspect_page(name, url):
    user_dir = os.path.abspath(f"./scratch/{name}_session")
    os.makedirs(user_dir, exist_ok=True)
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=True,
            args=CHROMIUM_STEALTH_ARGS,
            viewport={'width': 1366, 'height': 768}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script(STEALTH_JS_INIT)
        
        apis = []
        async def on_response(response):
            try:
                ct = response.headers.get("content-type", "")
                if "application/json" in ct and ("job" in response.url.lower() or "search" in response.url.lower() or "feed" in response.url.lower()):
                    apis.append(response.url)
            except Exception:
                pass
        page.on("response", on_response)

        try:
            print(f"\n--- Inspecting {name}: {url} ---")
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(6)
            
            print(f"Title: {await page.title()}")
            print(f"Final URL: {page.url}")
            
            if apis:
                print(f"Intercepted {len(apis)} JSON APIs:")
                for a in apis[:5]:
                    print("  ->", a[:120])
                    
            html = await page.content()
            print(f"HTML length: {len(html)}")
            
            with open(f"./scratch/{name}_sample.html", "w", encoding="utf-8") as f:
                f.write(html)
            print(f"Saved sample HTML to ./scratch/{name}_sample.html")
            
        except Exception as e:
            print(f"Error inspecting {name}: {e}")
        finally:
            await context.close()

async def main():
    sites = [
        ("foundit", "https://www.foundit.in/srp/results?query=python&locations=bangalore"),
        ("apna", "https://apna.co/jobs?search=true&text=python&location=Bengaluru"),
        ("shine", "https://www.shine.com/job-search/python-jobs-in-bangalore"),
        ("timesjobs", "https://www.timesjobs.com/candidate/job-search.html?searchType=personalizedSearch&from=submit&txtKeywords=python&txtLocation=bangalore"),
        ("careerjet", "https://www.careerjet.co.in/search/jobs?s=python&l=bangalore"),
        ("dice", "https://www.dice.com/jobs?q=python&location=Remote"),
        ("simplyhired", "https://www.simplyhired.co.in/search?q=python&l=bangalore")
    ]
    for name, url in sites:
        await inspect_page(name, url)

asyncio.run(main())
