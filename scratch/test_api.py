import asyncio
import json
import os
import sys
sys.path.append(os.path.abspath("."))
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS

async def test_api():
    user_dir = os.path.abspath("./himalayas_session")
    os.makedirs(user_dir, exist_ok=True)
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=True,
            args=CHROMIUM_STEALTH_ARGS,
            viewport={'width': 1366, 'height': 768}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Test API search endpoint
        api_url = "https://himalayas.app/jobs/api/search?q=Software+Development&country=United+Kingdom"
        print(f"Testing API URL: {api_url}")
        
        response = await page.goto(api_url)
        print(f"Status: {response.status}")
        text = await page.content()
        # Extract pre tag or raw text if JSON
        try:
            body_text = await page.inner_text("body")
            data = json.loads(body_text)
            print(f"[+] Successfully loaded JSON!")
            print(f"Keys in response: {list(data.keys()) if isinstance(data, dict) else len(data)}")
            if isinstance(data, dict):
                jobs = data.get("jobs", [])
                print(f"Jobs returned in JSON: {len(jobs)}")
                if jobs:
                    print("Sample job 1:")
                    print(json.dumps(jobs[0], indent=2))
                print(f"Total count: {data.get('total_count', 'N/A')}")
        except Exception as e:
            print(f"JSON Parse Error: {e}")
            print(f"Body text sample: {text[:500]}")
            
        await context.close()

if __name__ == "__main__":
    asyncio.run(test_api())
