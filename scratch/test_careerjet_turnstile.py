import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS
from bs4 import BeautifulSoup

async def test():
    user_dir = os.path.abspath("./careerjet_session_test")
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
        await page.goto("https://www.careerjet.co.in/", timeout=30000)
        print('Waiting for Turnstile solve on homepage...')
        await asyncio.sleep(8)
        
        url = 'https://www.careerjet.co.in/jobs?s=Sales+Executive&l=Bangalore'
        print('Navigating to search URL:', url)
        await page.goto(url, timeout=30000)
        await asyncio.sleep(6)
        print('Search Page Title:', await page.title())
        content = await page.content()
        s = BeautifulSoup(content, 'html.parser')
        cards = s.select("article.job, .job-list article, article, .job")
        print('Cards found:', len(cards))
        for c in cards[:5]:
            h2 = c.select_one("h2 a, a.title, h2")
            if h2:
                print('Job:', h2.text.strip())
        await context.close()

if __name__ == "__main__":
    asyncio.run(test())
