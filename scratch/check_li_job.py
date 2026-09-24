import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from utils import CHROMIUM_STEALTH_ARGS, create_stealth_context

async def check():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        context = await create_stealth_context(browser)
        page = await context.new_page()
        url = "https://www.linkedin.com/jobs/view/4467734025"
        print("Checking", url)
        await page.goto(url)
        await asyncio.sleep(5)
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        # Look for workplace type / remote badge
        print("Title:", soup.find('h1').text.strip() if soup.find('h1') else 'No H1')
        workplace = soup.find_all(class_=lambda x: x and ('workplace' in x.lower() or 'job-insight' in x.lower() or 'bullet' in x.lower()))
        for w in workplace:
            print("Insight:", w.text.strip())
        await browser.close()

asyncio.run(check())
