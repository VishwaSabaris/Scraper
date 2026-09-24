import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("."))
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, STEALTH_JS_INIT

async def inspect_careerjet():
    proxy_url = "http://8.215.25.3:2080"
    user_dir = os.path.abspath("./careerjet_proxy_test_session")
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=True,
            channel="chrome",
            args=CHROMIUM_STEALTH_ARGS,
            viewport={'width': 1366, 'height': 768},
            proxy={"server": proxy_url}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script(STEALTH_JS_INIT)

        print("[*] Navigating to Careerjet search...")
        url = "https://www.careerjet.co.in/jobs?s=Sales+Development+Representative&l=Bangalore"
        await page.goto(url, timeout=35000)
        await asyncio.sleep(6)
        
        title = await page.title()
        print(f"[*] Title: {title}")
        print(f"[*] URL: {page.url}")
        
        # Check for Turnstile / Cloudflare / CAPTCHA
        content = await page.content()
        has_turnstile = "cf-turnstile" in content or "challenges.cloudflare.com" in content or "turnstile" in content.lower()
        has_captcha = "captcha" in content.lower()
        print(f"[*] Cloudflare / Turnstile detected: {has_turnstile}")
        print(f"[*] Captcha detected: {has_captcha}")
        
        # Save screenshot and snippet
        await page.screenshot(path="scratch/careerjet_proxy_view.png")
        print("[*] Screenshot saved to scratch/careerjet_proxy_view.png")
        
        text_preview = await page.evaluate("() => document.body ? document.body.innerText.slice(0, 500) : ''")
        print("\n--- Page Text Snippet ---")
        print(text_preview)
        print("-------------------------\n")
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(inspect_careerjet())
