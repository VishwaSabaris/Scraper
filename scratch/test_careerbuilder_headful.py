import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS

async def test():
    user_dir = os.path.abspath("./careerbuilder_session_test")
    os.makedirs(user_dir, exist_ok=True)
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=False,
            channel="chrome",
            args=CHROMIUM_STEALTH_ARGS,
            viewport={'width': 1366, 'height': 768}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        url = 'https://www.careerbuilder.com/jobs?keywords=Sales&location=Chicago'
        print('Navigating to', url, 'headless=False...')
        await page.goto(url, timeout=30000)
        await asyncio.sleep(5)
        print('Title:', await page.title(), 'URL:', page.url)
        content = await page.content()
        from bs4 import BeautifulSoup
        s = BeautifulSoup(content, 'html.parser')
        cards = s.find_all('article', {'data-testid': 'JobCard'})
        print('data-testid JobCard:', len(cards))
        print('all article elements:', len(s.find_all('article')))
        print('links with /job/:', len(s.select('a[href*="/job/"]')))
        await context.close()

if __name__ == "__main__":
    asyncio.run(test())
