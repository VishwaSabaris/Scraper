import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from utils import CHROMIUM_STEALTH_ARGS

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
        page = await browser.new_page()
        try:
            print('Navigating to Naukri search page...')
            await page.goto('https://www.naukri.com/software-engineer-jobs-in-bangalore', timeout=40000)
            await asyncio.sleep(4)
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for filter sidebar or filter groups
            # On Naukri, filters are often in a container like .styles_filter-wrapper__ or #filter-wrapper or [data-filter-id]
            filter_groups = soup.select('[data-filter-id], [class*="filter-group"], [class*="filterGroup"], [class*="styles_filter"], [class*="facets"]')
            print('Found filter groups:', len(filter_groups))
            
            # Extract all filter group headers and their options
            all_filters = {}
            for fg in filter_groups:
                header = fg.select_one('[class*="heading"], [class*="title"], h3, h4, span')
                header_text = header.text.strip() if header else "Unknown"
                opts = [opt.text.strip() for opt in fg.select('label, a, span[class*="opt"]') if opt.text.strip()]
                if header_text and opts:
                    all_filters[header_text] = opts[:10]
            
            if not all_filters:
                # Broader search for filters
                print("Broad search...")
                for sec in soup.select('div[class*="filter"], section[class*="filter"], div[class*="facet"]'):
                    txt = sec.text.strip()
                    if any(k in txt.lower() for k in ['experience', 'work mode', 'salary', 'department', 'education', 'posted by', 'freshness']):
                        print("Section sample:", txt[:200])
                        print("-" * 50)
            else:
                for k, v in all_filters.items():
                    print(f"Filter: {k} -> {v}")

        except Exception as e:
            print('Error:', e)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test())
