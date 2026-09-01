import asyncio
import os
import sys
sys.path.append(os.path.abspath("."))
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS

async def test_zip():
    user_dir = os.path.abspath("./ziprecruiter_session")
    os.makedirs(user_dir, exist_ok=True)
    
    url = "https://www.ziprecruiter.com/jobs-search?search=Software+Developer&location=London"
    print(f"[*] Navigating to: {url}")
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=False,
            channel="chrome",
            args=CHROMIUM_STEALTH_ARGS,
            viewport={'width': 1366, 'height': 768}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        try:
            resp = await page.goto(url, timeout=40000)
            print(f"Status: {resp.status if resp else 'None'}")
            print(f"Page Title: {await page.title()}")
            print(f"Final URL: {page.url}")
            
            # Wait for content to load
            await asyncio.sleep(5)
            
            # Check for job list container
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            
            # Print title tag, heading, and job card candidates
            job_cards = soup.find_all(class_=lambda c: c and ("job_result" in c or "job-card" in c or "job_listing" in c or "job_item" in c or "job-item" in c or "job_content" in c))
            print(f"Job cards with class containing job/card: {len(job_cards)}")
            
            # Check article tag or div tag with data-testid
            cards_by_testid = soup.find_all(attrs={"data-testid": lambda t: t and "job-card" in t})
            print(f"Cards matching data-testid 'job-card': {len(cards_by_testid)}")
            
            all_articles = soup.find_all("article")
            print(f"Articles count: {len(all_articles)}")
            
            # Find all links on page
            all_links = soup.find_all("a", href=True)
            job_links = [a for a in all_links if "/job/" in a["href"] or "lk=" in a["href"] or "/jobs-search" in a["href"]]
            print(f"Total job-related links found: {len(job_links)}")
            
            for idx, link in enumerate(job_links[:10]):
                href = link.get("href")
                text = link.get_text(strip=True)
                print(f"  Link {idx+1}: text='{text[:40]}' | href='{href}'")
                
            # If job_cards exist, print details of first 3
            cards_to_inspect = cards_by_testid or all_articles or job_cards
            if cards_to_inspect:
                print(f"\n--- Inspecting {len(cards_to_inspect)} card elements ---")
                for i, card in enumerate(cards_to_inspect[:5]):
                    print(f"\nCard {i+1}: Tag={card.name} | class={card.get('class')} | data-testid={card.get('data-testid')}")
                    # Find title
                    h2 = card.find(["h2", "h3", "h4", "a"])
                    print("  Title text:", h2.get_text(strip=True) if h2 else "N/A")
                    
                    # Find company
                    comp = card.find(attrs={"data-testid": lambda t: t and "company" in t}) or card.find(class_=lambda c: c and "company" in c)
                    print("  Company:", comp.get_text(strip=True) if comp else "N/A")
                    
                    # Find location
                    loc = card.find(attrs={"data-testid": lambda t: t and "location" in t}) or card.find(class_=lambda c: c and "location" in c)
                    print("  Location:", loc.get_text(strip=True) if loc else "N/A")
                    
                    # Find salary
                    sal = card.find(attrs={"data-testid": lambda t: t and "salary" in t}) or card.find(class_=lambda c: c and ("salary" in c or "pay" in c))
                    print("  Salary:", sal.get_text(strip=True) if sal else "N/A")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(test_zip())
