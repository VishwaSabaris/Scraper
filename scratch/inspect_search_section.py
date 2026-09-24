import asyncio
from playwright.async_api import async_playwright

async def inspect_ui():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://wellfound.com/jobs", wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        info = await page.evaluate('''() => {
            const forms = Array.from(document.querySelectorAll('form')).map(f => f.outerHTML.slice(0, 500));
            const searchSection = document.querySelector('button')?.closest('div')?.parentElement?.innerText || '';
            const allSelects = Array.from(document.querySelectorAll('[class*="select"]')).map(e => ({
                text: e.innerText,
                className: e.className
            }));
            return { forms, searchSection: searchSection.slice(0, 1000), allSelects: allSelects.slice(0, 10) };
        }''')
        
        print("Search section:", info['searchSection'])
        print("\nAll selects:", info['allSelects'])
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_ui())
