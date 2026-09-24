import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def inspect_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://wellfound.com/jobs", wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        inputs = await page.eval_on_selector_all("input", "elements => elements.map(e => ({placeholder: e.placeholder, name: e.name, type: e.type, id: e.id, class: e.className}))")
        print("Inputs found:", inputs)
        
        buttons = await page.eval_on_selector_all("button", "elements => elements.map(e => e.innerText.trim()).filter(t => t.length > 0)")
        print("Buttons found:", buttons[:10])
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_page())
