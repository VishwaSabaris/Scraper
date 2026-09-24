import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from utils import CHROMIUM_STEALTH_ARGS, is_role_match

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        page = await b.new_page()
        url = "https://www.workatastartup.com/companies?demographic=any&hasEquity=any&hasSalary=any&industry=any&interviewProcess=any&jobType=any&layout=list-compact&locations=Remote&query=Software+Engineer&sortBy=keyword&tab=any&usVisaNotRequired=any"
        await page.goto(url)
        await asyncio.sleep(4)
        soup = BeautifulSoup(await page.content(), 'html.parser')
        
        job_links = soup.find_all('a', href=lambda h: h and re.search(r'/jobs/\d+', h))
        print("Total job links:", len(job_links))
        
        extracted = []
        for jl in job_links:
            apply_link = "https://www.workatastartup.com" + jl['href'] if jl['href'].startswith('/') else jl['href']
            
            # Check Layout 1 (Self-contained job card: <a> contains company, title, meta)
            h3 = jl.find(['h3', 'h2'])
            comp_el = jl.find('p', class_=lambda c: c and 'font-semibold' in c)
            img = jl.find('img')
            
            comp_name = "YC Startup"
            job_title = ""
            tagline = ""
            meta_text = ""
            
            if h3:
                job_title = h3.text.strip()
            if comp_el:
                comp_name = comp_el.text.strip()
            elif img and img.get('alt'):
                comp_name = img['alt'].replace(' logo', '').replace(' Logo', '').strip()
                
            # If not found inside jl, check Parent / Card container (Layout 2)
            if not job_title:
                job_title = jl.text.strip()
            if comp_name == "YC Startup":
                card = jl.parent
                for _ in range(8):
                    if not card:
                        break
                    # Look for company link in card
                    for ca in card.find_all('a', href=lambda h: h and re.search(r'/companies/[a-zA-Z0-9_-]+$', h)):
                        txt = ca.text.strip()
                        txt_lower = txt.lower()
                        if txt_lower.startswith('see all') or txt_lower.startswith('view job') or txt_lower == 'apply':
                            continue
                        if len(txt) > 1:
                            parts = re.split(r'[\u2022\u2013\u2014|\t\n\xb7]', txt)
                            comp_name = re.sub(r'\s*\([A-Z0-9]+\).*', '', parts[0]).strip()
                            break
                    if comp_name != "YC Startup":
                        break
                    card = card.parent

            # Location and salary extraction
            line_clamp = jl.find(class_=lambda c: c and 'line-clamp-2' in c)
            meta_text = line_clamp.text.strip() if line_clamp else jl.text.strip()
            
            loc = "Remote"
            tokens = [t.strip() for t in re.split(r'[•\xb7|\n]', meta_text) if t.strip()]
            for t in tokens:
                if any(c in t for c in ['Austin', 'San Francisco', 'New York', 'London', 'Remote', 'US', 'CA', 'India', 'Worldwide']):
                    loc = t
                    break
                    
            extracted.append({
                "title": job_title,
                "company": comp_name,
                "location": loc,
                "meta": meta_text,
                "apply": apply_link
            })
            
        print(f"Extracted {len(extracted)} jobs:")
        for ex in extracted[:10]:
            print(f"  Role: {ex['title']:<35} | Company: {ex['company']:<25} | Loc: {ex['location']:<20}")
            
        await b.close()

if __name__ == "__main__":
    asyncio.run(run())
