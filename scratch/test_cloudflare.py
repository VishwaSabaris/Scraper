import asyncio
import os
import sys
sys.path.append(os.path.abspath("."))
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS

async def test_cloudflare_bypass():
    user_dir = os.path.abspath("./himalayas_session")
    os.makedirs(user_dir, exist_ok=True)
    
    async with async_playwright() as p:
        # Pass extra stealth parameters
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=False,
            channel="chrome",
            args=CHROMIUM_STEALTH_ARGS + [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ],
            viewport={'width': 1366, 'height': 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Inject stealth evasions
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        url = "https://himalayas.app/jobs/countries/united-kingdom/software-development?view=filters&src=adv"
        print(f"Navigating to: {url}")
        
        try:
            await page.goto(url, timeout=45000, wait_until="domcontentloaded")
            
            # Wait up to 15 seconds if Cloudflare challenge is present
            for i in range(15):
                title = await page.title()
                print(f"[{i}s] Title: {title}")
                if "Just a moment" not in title:
                    print("[+] Challenge passed or not present!")
                    break
                await asyncio.sleep(1)
                
            # Wait for content to settle
            await asyncio.sleep(3)
            
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            
            articles = soup.find_all("article")
            print(f"Articles count (<article>): {len(articles)}")
            
            if articles:
                print(f"[+] Found {len(articles)} articles!")
                for idx, art in enumerate(articles[:5]):
                    # Try to extract title, company, link
                    title_elem = art.find("a", href=lambda h: h and "/jobs/" in h)
                    print(f" Article {idx+1}: {title_elem.get_text(strip=True) if title_elem else 'No title'} | href={title_elem.get('href') if title_elem else ''}")
            else:
                print("[-] Still 0 articles. Let's inspect page links:")
                links = soup.find_all("a", href=True)
                job_links = [l.get("href") for l in links if "/jobs/" in l.get("href")]
                print(f"Total job links found: {len(job_links)}")
                if job_links:
                    print("Sample job links:", job_links[:10])
                else:
                    print("Page body preview:")
                    print(soup.get_text(separator=' ', strip=True)[:400])

        except Exception as e:
            print(f"Error during execution: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(test_cloudflare_bypass())
