import asyncio
import os
import sys
import json
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context

async def inspect_cb_deep():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        context = await create_stealth_context(browser)
        page = await context.new_page()
        
        captured_json = []
        
        async def on_response(res):
            try:
                ct = res.headers.get("content-type", "")
                if "json" in ct or "javascript" in ct:
                    if "job" in res.url.lower() or "search" in res.url.lower() or "graphql" in res.url.lower():
                        text = await res.text()
                        if "title" in text.lower() or "job" in text.lower():
                            captured_json.append({"url": res.url, "len": len(text), "sample": text[:300]})
            except Exception:
                pass
                
        page.on("response", on_response)
        
        u = "https://www.careerbuilder.com/job-listings/search?q=Sales+Development+Representative"
        print("Navigating to:", u)
        await page.goto(u, timeout=30000, wait_until="networkidle")
        await asyncio.sleep(5)
        
        print("Captured network calls:", len(captured_json))
        for c in captured_json:
            print("  URL:", c["url"])
            print("  Sample:", c["sample"][:150])
            
        container_html = await page.evaluate("() => document.getElementById('card-scroll-container') ? document.getElementById('card-scroll-container').innerHTML : 'NO CONTAINER'")
        print("Container HTML len:", len(container_html))
        print("Container HTML snippet:", container_html[:500])
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_cb_deep())
