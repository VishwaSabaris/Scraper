import asyncio
from playwright.async_api import async_playwright

async def get_links():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://wellfound.com/jobs", wait_until="domcontentloaded")
        await asyncio.sleep(2)
        
        links = await page.eval_on_selector_all("a", "elements => elements.map(e => ({href: e.href, text: e.innerText.trim()}))")
        
        for l in links:
            if any(x in l['href'] for x in ['/role/', '/location/', '/jobs/']):
                print(f"{l['text']} -> {l['href']}")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_links())
