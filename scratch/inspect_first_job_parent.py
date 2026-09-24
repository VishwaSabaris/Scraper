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
        soup = BeautifulSoup(await page.content(), 'html.parser')
        job_links = soup.find_all('a', href=lambda h: h and '/jobs/' in h)
        print("Total job links:", len(job_links))
        if job_links:
            jl = job_links[0]
            print("First job link:", jl['href'], repr(jl.text.strip()))
            p = jl
            for i in range(12):
                p = p.parent
                if not p:
                    break
                comp_a = [a for a in p.find_all('a') if a.get('href') and '/companies/' in a['href']]
                if comp_a:
                    print(f"Parent {i+1} (<{p.name} class='{p.get('class')}'>) has {len(comp_a)} company links:")
                    for ca in comp_a:
                        print(f"  href: {ca['href']} | text: {repr(ca.text.strip())}")
                    break
        await b.close()

if __name__ == "__main__":
    asyncio.run(run())
