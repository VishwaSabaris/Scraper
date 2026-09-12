import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json

async def test_sites():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 1. Foundit
        print("=== PLAYWRIGHT: Foundit ===")
        try:
            await page.goto("https://www.foundit.in/srp/results?query=Python&locations=Bangalore", timeout=25000)
            await asyncio.sleep(4)
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            cards = soup.select('.srpResultCard') or soup.select('[class*="srpResultCard"]') or soup.select('[class*="jobTuple"]') or soup.select('.cardContainer')
            print(f"Foundit PW cards: {len(cards)}")
            if cards:
                c = cards[0]
                title = c.select_one('.jobTitle') or c.select_one('[class*="title"]') or c.select_one('a')
                comp = c.select_one('.companyName') or c.select_one('[class*="company"]')
                loc = c.select_one('.location') or c.select_one('[class*="location"]')
                print("Sample Foundit:", title.text.strip() if title else '', "|", comp.text.strip() if comp else '', "|", loc.text.strip() if loc else '')
        except Exception as e:
            print("Foundit PW err:", e)

        # 2. Instahyre
        print("\n=== PLAYWRIGHT: Instahyre ===")
        try:
            await page.goto("https://www.instahyre.com/search-jobs/?search=true&job_type=0&skills=Python", timeout=25000)
            await asyncio.sleep(4)
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            cards = soup.select('.employer-row') or soup.select('.opportunity-container') or soup.select('[id^="job-"]') or soup.select('.job-card') or soup.select('.employer-notes')
            print(f"Instahyre PW cards: {len(cards)}")
            if cards:
                c = cards[0]
                title = c.select_one('.employer-job-title') or c.select_one('.opportunity-title') or c.select_one('h3') or c.select_one('a')
                comp = c.select_one('.employer-name') or c.select_one('.company-name')
                print("Sample Instahyre:", title.text.strip() if title else '', "|", comp.text.strip() if comp else '')
        except Exception as e:
            print("Instahyre PW err:", e)

        # 3. Dice
        print("\n=== PLAYWRIGHT: Dice ===")
        try:
            await page.goto("https://www.dice.com/jobs?q=Python&location=Remote", timeout=25000)
            await asyncio.sleep(4)
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            cards = soup.select('dhi-search-card') or soup.select('[data-cy="search-card"]') or soup.select('.search-card') or soup.select('a[data-cy="card-title-link"]')
            print(f"Dice PW cards: {len(cards)}")
            if cards:
                c = cards[0]
                title = c.select_one('[data-cy="card-title-link"]') or c.select_one('.card-title-link') or c.select_one('a')
                comp = c.select_one('[data-cy="search-result-company-name"]') or c.select_one('.card-company')
                print("Sample Dice:", title.text.strip() if title else '', "|", comp.text.strip() if comp else '')
        except Exception as e:
            print("Dice PW err:", e)

        # 4. SimplyHired
        print("\n=== PLAYWRIGHT: SimplyHired ===")
        try:
            await page.goto("https://www.simplyhired.co.in/search?q=Python&l=Bengaluru", timeout=25000)
            await asyncio.sleep(4)
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            cards = soup.select('[data-testid="searchSerpJob"]') or soup.select('li[data-testid="searchSerpJob"]') or soup.select('.SerpJob-jobCard')
            print(f"SimplyHired PW cards: {len(cards)}")
            if cards:
                c = cards[0]
                title = c.select_one('[data-testid="searchSerpJobTitle"]') or c.select_one('h2 a') or c.select_one('h2')
                comp = c.select_one('[data-testid="searchSerpJobCompany"]') or c.select_one('[data-testid="companyName"]') or c.select_one('.css-1t925in')
                print("Sample SimplyHired:", title.text.strip() if title else '', "|", comp.text.strip() if comp else '')
        except Exception as e:
            print("SimplyHired PW err:", e)

        # 5. TimesJobs
        print("\n=== PLAYWRIGHT: TimesJobs ===")
        try:
            await page.goto("https://www.timesjobs.com/candidate/job-search.html?searchType=personalizedSearch&from=submit&txtKeywords=Python&txtLocation=Bangalore", timeout=25000)
            await asyncio.sleep(4)
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            cards = soup.select('li.clearfix.job-bx') or soup.select('.job-bx') or soup.select('[class*="job-bx"]') or soup.select('ul.job-list li')
            print(f"TimesJobs PW cards: {len(cards)}")
            if cards:
                c = cards[0]
                title = c.select_one('h2 a') or c.select_one('h2')
                comp = c.select_one('.heading-trun') or c.select_one('h3')
                print("Sample TimesJobs:", title.text.strip() if title else '', "|", comp.text.strip() if comp else '')
        except Exception as e:
            print("TimesJobs PW err:", e)

        # 6. Careerjet
        print("\n=== PLAYWRIGHT: Careerjet ===")
        try:
            await page.goto("https://www.careerjet.co.in/search/jobs?s=Python&l=Bangalore", timeout=25000)
            await asyncio.sleep(4)
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            cards = soup.select('article.job') or soup.select('.job-list article') or soup.select('article')
            print(f"Careerjet PW cards: {len(cards)}")
            if cards:
                c = cards[0]
                title = c.select_one('header h2 a') or c.select_one('h2 a') or c.select_one('h2')
                comp = c.select_one('.company_compact') or c.select_one('.company') or c.select_one('p.company')
                print("Sample Careerjet:", title.text.strip() if title else '', "|", comp.text.strip() if comp else '')
        except Exception as e:
            print("Careerjet PW err:", e)

        await browser.close()

asyncio.run(test_sites())
