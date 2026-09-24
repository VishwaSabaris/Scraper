import asyncio
import json
import sys
import os
sys.path.insert(0, os.path.abspath("."))
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS

async def inspect():
    async with async_playwright() as p:
        user_dir = "./naukri_session"
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=True,
            args=CHROMIUM_STEALTH_ARGS,
            viewport={'width': 1366, 'height': 768}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        target_url = "https://www.naukri.com/data-analyst-jobs-in-bangalore?k=data%20analyst&l=bangalore"
        print(f"Navigating to {target_url}...")
        try:
            await page.goto(target_url, timeout=35000)
            await asyncio.sleep(5)
            
            title = await page.title()
            print(f"Page Title: {title}")
            url = page.url
            print(f"Final URL: {url}")
            body_len = await page.evaluate("() => document.body.innerHTML.length")
            print(f"Body innerHTML length: {body_len}")
            
            # Let's find all elements matching filters or sidebar
            filter_data = await page.evaluate('''() => {
                const results = [];
                // Look for all filter sections
                document.querySelectorAll('div[class*="styles_filter-group"], div[class*="filterBlock"], div[class*="styles_filter-container"]').forEach(section => {
                    const heading = section.querySelector('span, h3, p, div[class*="title"]');
                    const title = heading ? heading.textContent.trim() : 'Unknown';
                    const items = [];
                    section.querySelectorAll('label, div[class*="styles_checkbox-wrapper"], a[class*="styles_filter-item"]').forEach(item => {
                        const input = item.querySelector('input') || item;
                        items.push({
                            label: item.textContent.trim(),
                            id: input.id || null,
                            dataId: item.getAttribute('data-id') || input.getAttribute('data-id') || null,
                            name: input.getAttribute('name') || null,
                            value: input.getAttribute('value') || null,
                            href: item.getAttribute('href') || (item.querySelector('a') ? item.querySelector('a').getAttribute('href') : null)
                        });
                    });
                    if (items.length > 0) {
                        results.push({ section: title, items: items.slice(0, 10) });
                    }
                });
                return results;
            }''')
            print("Found filter sections:")
            print(json.dumps(filter_data, indent=2))

            # Also let's inspect all links (a tags) in the filter area to see what URLs they point to!
            filter_links = await page.evaluate('''() => {
                const links = [];
                document.querySelectorAll('a[href*="wfhType"], a[href*="experience"], a[href*="ctcFilter"], a[href*="salary"], a[href*="glbl_qcpr_filter"], a[href*="ugc_department"], a[href*="department"], a[href*="functionalAreaGid"]').forEach(a => {
                    links.push({
                        text: a.textContent.trim(),
                        href: a.href
                    });
                });
                return links.slice(0, 30);
            }''')
            print("\nFilter links matching query patterns:")
            print(json.dumps(filter_links, indent=2))

            # Also let's find any a tag inside the left filter container
            left_links = await page.evaluate('''() => {
                const links = [];
                const left = document.querySelector('div[class*="styles_left-section"], div[class*="filter-container"]');
                if (left) {
                    left.querySelectorAll('a').forEach(a => {
                        if (a.href && a.href.includes('http')) {
                            links.push({
                                text: a.textContent.trim(),
                                href: a.href
                            });
                        }
                    });
                }
                return links.slice(0, 40);
            }''')
            print("\nLeft filter links sample:")
            print(json.dumps(left_links, indent=2))
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(inspect())
