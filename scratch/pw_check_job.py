import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from utils import CHROMIUM_STEALTH_ARGS

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        page = await b.new_page()
        await page.goto('https://www.workatastartup.com/jobs/62175')
        await asyncio.sleep(4)
        s = BeautifulSoup(await page.content(), 'html.parser')
        print("Page title:", s.title.text if s.title else "No title")
        for a in s.find_all('a', href=lambda h: h and '/companies/' in h):
            print(f"Company link on job page: {a.text.strip()} -> {a['href']}")
        await b.close()

if __name__ == "__main__":
    asyncio.run(run())
