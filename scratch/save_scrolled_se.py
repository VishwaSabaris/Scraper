import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        page = await b.new_page()
        url = "https://www.workatastartup.com/companies?demographic=any&hasEquity=any&hasSalary=any&industry=any&interviewProcess=any&jobType=any&layout=list-compact&locations=Remote&query=Software+Engineer&sortBy=keyword&tab=any&usVisaNotRequired=any"
        await page.goto(url)
        await asyncio.sleep(4)
        for _ in range(2):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
        html = await page.content()
        with open("scratch/scrolled_se.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Saved scratch/scrolled_se.html")
        await b.close()

if __name__ == "__main__":
    asyncio.run(run())
