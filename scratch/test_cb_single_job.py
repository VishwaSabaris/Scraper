import asyncio
import json
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import CHROMIUM_STEALTH_ARGS

async def test_job(url):
    print(f"Opening: {url}")
    user_dir = "./careerbuilder_session_test"
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=True,
            args=CHROMIUM_STEALTH_ARGS,
            viewport={'width': 1366, 'height': 768}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        try:
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(4)
            
            title = await page.title()
            print("Final URL:", page.url)
            print("Page Title:", title)
            
            html = await page.content()
            print("HTML Length:", len(html))
            print("HTML snippet:\n", html[:1000])
            soup = BeautifulSoup(html, 'html.parser')
            
            # Check for __NEXT_DATA__
            next_data = soup.find('script', id='__NEXT_DATA__')
            if next_data:
                print("Found __NEXT_DATA__! Length:", len(next_data.string or ""))
                try:
                    data = json.loads(next_data.string)
                    with open("scratch/cb_job_next_data.json", "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    print("Saved scratch/cb_job_next_data.json")
                except Exception as e:
                    print("Error parsing __NEXT_DATA__:", e)
                    
            # Check JSON-LD
            json_lds = soup.find_all('script', type='application/ld+json')
            print(f"Found {len(json_lds)} JSON-LD scripts")
            for i, jld in enumerate(json_lds):
                try:
                    jd = json.loads(jld.string)
                    print(f"JSON-LD [{i}] type:", jd.get('@type'))
                    if jd.get('@type') == 'JobPosting' or 'hiringOrganization' in jd:
                        print("Hiring Org:", jd.get('hiringOrganization'))
                        print("Job Title:", jd.get('title'))
                        print("Description length:", len(jd.get('description', '')))
                except Exception as e:
                    pass

            # Check DOM selectors
            h1 = soup.find('h1')
            print("H1:", h1.text.strip() if h1 else None)
            
            # Look for company name selectors
            comp_candidates = soup.find_all(attrs={"data-testid": re.compile("company", re.I)})
            print(f"data-testid company candidates: {len(comp_candidates)}")
            for c in comp_candidates:
                print("Comp candidate:", c.get('data-testid'), "->", c.text.strip())

            # Look for job description selectors
            desc_candidates = soup.find_all(attrs={"data-testid": re.compile("description|job-details", re.I)})
            print(f"data-testid desc candidates: {len(desc_candidates)}")
            for d in desc_candidates:
                print("Desc candidate:", d.get('data-testid'), "-> len:", len(d.text.strip()))
                
            # If no data-testid, look for classes
            desc_div = soup.find('div', class_=re.compile("job-description|description", re.I))
            if desc_div:
                print("Found class description len:", len(desc_div.text.strip()))
                
        except Exception as e:
            print("Error loading page:", e)
        finally:
            await context.close()

if __name__ == "__main__":
    url = "https://www.careerbuilder.com/job-details/senior-data-engineer-london-england-london-ky--82dfb563-6832-4b57-bda6-2e30aa4a818d"
    asyncio.run(test_job(url))
