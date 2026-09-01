import asyncio
import os
import sys
sys.path.append(os.path.abspath("."))
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS

async def test_jobleads_urls():
    user_dir = os.path.abspath("./jobleads_session")
    os.makedirs(user_dir, exist_ok=True)
    
    urls_to_test = [
        "https://www.jobleads.com/gb/jobs/l/United%20Kingdom%2C%20UK/q/Software%20Developer",
        "https://www.jobleads.com/gb/jobs/l/United%20Kingdom/q/Software%20Developer",
        "https://www.jobleads.com/gb/jobs/q/Software%20Developer",
        "https://www.jobleads.com/uk/jobs/q/Software%20Developer%20United%20Kingdom"
    ]
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=True,
            args=CHROMIUM_STEALTH_ARGS,
            viewport={'width': 1366, 'height': 768}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        for url in urls_to_test:
            print(f"\n--- Testing URL: {url} ---")
            response = await page.goto(url, timeout=30000)
            print(f"Final URL after goto: {page.url}")
            await asyncio.sleep(4)
            
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.find_all(class_="animated-list-item")
            if not cards:
                cards = soup.find_all(attrs={"data-testid": "search-job-card"})
            print(f"Card count: {len(cards)}")
            
            # Print sample link and location
            for card in cards[:3]:
                link_el = card.find(attrs={"data-testid": "search-job-card-link"}) or card.find("a", href=True)
                comp_loc_el = card.find(attrs={"data-testid": "search-job-card-company"})
                print("  Title:", link_el.text.strip() if link_el else "None")
                print("  Href:", link_el.get("href") if link_el else "None")
                print("  Comp/Loc:", comp_loc_el.text.strip() if comp_loc_el else "None")
                
        await context.close()

if __name__ == "__main__":
    asyncio.run(test_jobleads_urls())
