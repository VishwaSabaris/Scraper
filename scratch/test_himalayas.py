import asyncio
import os
import sys
sys.path.append(os.path.abspath("."))
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS

async def debug_url(url):
    print(f"=== Debugging URL: {url} ===")
    user_dir = os.path.abspath("./himalayas_session")
    os.makedirs(user_dir, exist_ok=True)
    
    async with async_playwright() as p:
        try:
            context = await p.chromium.launch_persistent_context(
                user_dir,
                headless=False,
                channel="chrome",
                args=CHROMIUM_STEALTH_ARGS,
                viewport={'width': 1366, 'height': 768}
            )
        except Exception:
            context = await p.chromium.launch_persistent_context(
                user_dir,
                headless=False,
                args=CHROMIUM_STEALTH_ARGS,
                viewport={'width': 1366, 'height': 768}
            )
            
        page = context.pages[0] if context.pages else await context.new_page()
        try:
            response = await page.goto(url, timeout=30000)
            print(f"Response Status: {response.status if response else 'None'}")
            await asyncio.sleep(5)
            
            html = await page.content()
            print(f"HTML length: {len(html)}")
            soup = BeautifulSoup(html, "html.parser")
            
            h1 = soup.find("h1")
            print(f"Page Title: {await page.title()}")
            print(f"Page H1: {h1.get_text(strip=True) if h1 else 'None'}")
            
            articles = soup.find_all("article")
            print(f"Articles count (<article>): {len(articles)}")
            
            if articles:
                sample = articles[0]
                print("First article snippet:")
                print(sample.prettify()[:1000])
            else:
                text = soup.get_text(separator=' ', strip=True)
                print(f"Page snippet: {text[:500]}")
                
                all_job_links = soup.find_all("a", href=lambda h: h and "/jobs/" in h)
                print(f"Total links with /jobs/: {len(all_job_links)}")
                for link in all_job_links[:10]:
                    print(f"  Link: href={link.get('href')} | text={link.get_text(strip=True)[:50]}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    url_to_test = sys.argv[1] if len(sys.argv) > 1 else "https://himalayas.app/jobs/countries/united-kingdom/software-development?view=filters&src=adv"
    asyncio.run(debug_url(url_to_test))
