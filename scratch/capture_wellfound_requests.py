import asyncio
from playwright.async_api import async_playwright

async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        urls = []
        page.on("request", lambda r: urls.append((r.method, r.url)))
        
        print("Navigating to https://wellfound.com/jobs...")
        try:
            await page.goto("https://wellfound.com/jobs", wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(4)
        except Exception as e:
            print("Nav error:", e)
        
        print(f"Captured {len(urls)} requests.")
        for method, url in urls:
            if any(x in url for x in ['graphql', 'api', 'wellfound.com']):
                print(f"{method} {url}")
                    
        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture())
