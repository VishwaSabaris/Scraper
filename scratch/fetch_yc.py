import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from utils import CHROMIUM_STEALTH_ARGS

async def fetch_yc():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        page = await b.new_page()
        url = "https://www.workatastartup.com/companies?demographic=any&hasEquity=any&hasSalary=any&industry=any&interviewProcess=any&jobType=any&layout=list-compact&locations=Remote&query=Python&sortBy=keyword&tab=any&usVisaNotRequired=any"
        print("Navigating to:", url)
        await page.goto(url, wait_until="domcontentloaded", timeout=40000)
        await asyncio.sleep(5)
        html = await page.content()
        with open("scratch/yc_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Saved scratch/yc_page.html, length:", len(html))
        await b.close()

if __name__ == "__main__":
    asyncio.run(fetch_yc())
