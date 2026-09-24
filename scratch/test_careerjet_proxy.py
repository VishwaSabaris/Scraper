import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.abspath("."))
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, STEALTH_JS_INIT
from bs4 import BeautifulSoup

TEST_PROXIES = [
    "http://8.215.25.3:2080",
    "http://45.194.41.16:8080",
    "http://45.194.41.43:8080",
]

async def test_careerjet_with_proxy(proxy_url, headless=True):
    print(f"\n=======================================================")
    print(f"Testing Careerjet via Proxy: {proxy_url}")
    print(f"=======================================================")

    user_dir = os.path.abspath("./careerjet_proxy_test_session")
    os.makedirs(user_dir, exist_ok=True)

    proxy_cfg = {"server": proxy_url}

    async with async_playwright() as p:
        launch_kwargs = {
            "headless": headless,
            "args": CHROMIUM_STEALTH_ARGS,
            "viewport": {'width': 1366, 'height': 768},
            "proxy": proxy_cfg
        }

        try:
            context = await p.chromium.launch_persistent_context(
                user_dir,
                channel="chrome",
                **launch_kwargs
            )
        except Exception as e:
            print(f"[*] Chrome channel failed ({e}), falling back to bundled chromium...")
            context = await p.chromium.launch_persistent_context(
                user_dir,
                **launch_kwargs
            )

        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script(STEALTH_JS_INIT)

        try:
            # Step 1: Verify IP reflection through browser
            print("[*] Step 1: Verifying browser IP reflection via proxy...")
            try:
                t0 = time.time()
                resp = await page.goto("https://api.ipify.org?format=json", timeout=20000)
                elapsed = time.time() - t0
                body = await page.text_content("body")
                print(f"[+] Proxy active! Browser observed IP: {body.strip()} (Latency: {elapsed:.2f}s)")
            except Exception as e:
                print(f"[!] Failed to connect through proxy: {e}")
                return False

            # Step 2: Visit Careerjet homepage to establish session / solve challenges
            print("\n[*] Step 2: Navigating to Careerjet homepage...")
            try:
                await page.goto("https://www.careerjet.co.in/", timeout=30000)
                await asyncio.sleep(5)
                title = await page.title()
                print(f"[+] Careerjet Homepage Title: {title}")
            except Exception as e:
                print(f"[!] Warning on homepage navigation: {e}")

            # Step 3: Search for jobs
            search_url = "https://www.careerjet.co.in/jobs?s=Sales+Development+Representative&l=Bangalore"
            print(f"\n[*] Step 3: Navigating to Careerjet search ({search_url})...")
            try:
                t0 = time.time()
                await page.goto(search_url, timeout=35000)
                await asyncio.sleep(4)
                await page.evaluate("window.scrollBy(0, 400);")
                await asyncio.sleep(2)
                elapsed = time.time() - t0

                title = await page.title()
                print(f"[+] Search Page Title: {title} (Loaded in {elapsed:.2f}s)")

                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")
                cards = soup.select("article.job, .job-list article, article, .job")
                print(f"[+] Found {len(cards)} job card elements on Careerjet!")

                extracted = 0
                for idx, card in enumerate(cards[:5], 1):
                    title_el = card.select_one("header h2 a, h2 a, a.title, h2")
                    comp_el = card.select_one(".company_compact, .company, p.company, a[href*='/company/']")
                    loc_el = card.select_one(".location_compact, .locations, ul.location")

                    if title_el:
                        t_text = title_el.text.strip()
                        c_text = comp_el.text.strip() if comp_el else "Unknown Company"
                        l_text = loc_el.text.strip() if loc_el else "Unknown Location"
                        print(f"    [{idx}] {t_text} | {c_text} ({l_text})")
                        extracted += 1

                if extracted > 0:
                    print(f"\n[SUCCESS] Proxy {proxy_url} successfully scraped {extracted} jobs from Careerjet!")
                    return True
                else:
                    print(f"[!] Warning: No job titles parsed from page.")
                    return False
            except Exception as e:
                print(f"[!] Error during Careerjet search: {e}")
                return False

        finally:
            await context.close()

async def main():
    target_proxy = sys.argv[1] if len(sys.argv) > 1 else TEST_PROXIES[0]
    success = await test_careerjet_with_proxy(target_proxy, headless=True)
    if not success and len(sys.argv) <= 1:
        # Try second working proxy if first fails
        print("\n[*] First proxy had issues, trying backup proxy...")
        await test_careerjet_with_proxy(TEST_PROXIES[1], headless=True)

if __name__ == "__main__":
    asyncio.run(main())
