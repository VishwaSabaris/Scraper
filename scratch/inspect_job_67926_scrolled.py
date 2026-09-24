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
        url = "https://www.workatastartup.com/companies?demographic=any&hasEquity=any&hasSalary=any&industry=any&interviewProcess=any&jobType=any&layout=list-compact&locations=Remote&query=Software+Engineer&sortBy=keyword&tab=any&usVisaNotRequired=any"
        await page.goto(url)
        await asyncio.sleep(4)
        for _ in range(2):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
        soup = BeautifulSoup(await page.content(), 'html.parser')
        jl = soup.find('a', href=lambda h: h and '/jobs/67926' in h)
        if jl:
            print("Found jl:", jl)
            print("jl.parent chain:")
            curr = jl
            for i in range(7):
                curr = curr.parent
                if not curr: break
                print(f"Parent {i+1} <{curr.name} class='{curr.get('class')}'>:")
                for a in curr.find_all('a'):
                    print(f"   a: href={a.get('href')} text={repr(a.text.strip())}")
        await b.close()

if __name__ == "__main__":
    asyncio.run(run())
