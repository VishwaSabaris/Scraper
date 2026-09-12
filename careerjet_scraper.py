import asyncio
import os
import sys
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, STEALTH_JS_INIT, save_to_csv, is_role_match

async def scrape_careerjet_jobs(job_role, location="", max_pages=1, headless=True, filter_params=None, **kwargs):
    """
    Scrapes job listings from careerjet.co.in using Playwright persistent context.
    Supports dynamic filter parameters and deep pagination.
    """
    fp = filter_params or {}
    effective_role = fp.get("s") or job_role
    effective_loc = fp.get("l") or location or ""
    
    print(f"[*] Careerjet: Fetching job listings for '{effective_role}' in '{effective_loc or 'Any'}'...")
    
    user_dir = os.path.abspath("./careerjet_session")
    os.makedirs(user_dir, exist_ok=True)
    
    jobs_data = []
    
    async with async_playwright() as p:
        try:
            context = await p.chromium.launch_persistent_context(
                user_dir,
                headless=headless,
                args=CHROMIUM_STEALTH_ARGS,
                viewport={'width': 1366, 'height': 768}
            )
        except Exception:
            context = await p.chromium.launch_persistent_context(
                user_dir,
                headless=headless,
                args=CHROMIUM_STEALTH_ARGS,
                viewport={'width': 1366, 'height': 768}
            )
            
        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script(STEALTH_JS_INIT)
        
        try:
            # First visit homepage to establish session
            try:
                await page.goto("https://www.careerjet.co.in/", timeout=20000)
                await asyncio.sleep(2)
            except Exception:
                pass
                
            for page_idx in range(1, max_pages + 1):
                params = {
                    "s": effective_role,
                    "p": page_idx
                }
                if effective_loc:
                    params["l"] = effective_loc
                for k in ["radius", "sort", "f"]:
                    if fp.get(k):
                        params[k] = fp[k]
                        
                url = f"https://www.careerjet.co.in/search/jobs?{urllib.parse.urlencode(params)}"
                print(f"[*] Careerjet: Navigating to page {page_idx} ({url})...")
                
                try:
                    await page.goto(url, timeout=35000)
                    await asyncio.sleep(4)
                    
                    # Scroll down to load elements
                    await page.evaluate("window.scrollBy(0, 400);")
                    await asyncio.sleep(1)
                    
                    html = await page.content()
                    soup = BeautifulSoup(html, "html.parser")
                    
                    cards = soup.select("article.job, .job-list article, article, .job")
                    print(f"[+] Careerjet: Found {len(cards)} card elements on page {page_idx}.")
                    
                    if not cards:
                        # Try page.evaluate fallback
                        js_cards = await page.evaluate('''() => {
                            const res = [];
                            document.querySelectorAll('article.job, article, .job').forEach(a => {
                                const h2 = a.querySelector('header h2 a, h2 a, a.title, h2');
                                const comp = a.querySelector('.company_compact, .company, p.company');
                                const loc = a.querySelector('.location_compact, .locations, ul.location');
                                const sal = a.querySelector('.salary, ul.salary');
                                const desc = a.querySelector('.desc, .job-description');
                                if (h2) {
                                    res.push({
                                        title: h2.innerText.trim(),
                                        link: h2.href || (h2.tagName === 'A' ? h2.href : ''),
                                        company: comp ? comp.innerText.trim() : 'Careerjet Employer',
                                        loc: loc ? loc.innerText.trim() : 'India',
                                        sal: sal ? sal.innerText.trim() : 'Not disclosed',
                                        desc: desc ? desc.innerText.trim() : ''
                                    });
                                }
                            });
                            return res;
                        }''')
                        if js_cards:
                            print(f"[+] Careerjet: JS evaluation found {len(js_cards)} cards.")
                            
                    added_on_page = 0
                    for card in cards:
                        title_el = card.select_one("header h2 a, h2 a, a.title, h2")
                        if not title_el:
                            continue
                            
                        title = title_el.text.strip()
                        if not is_role_match(title, job_role):
                            continue
                            
                        apply_link = title_el.get("href", "") if title_el.name == "a" else (title_el.find("a").get("href") if title_el.find("a") else "")
                        if apply_link and not apply_link.startswith("http"):
                            apply_link = "https://www.careerjet.co.in" + apply_link
                            
                        comp_el = card.select_one(".company_compact, .company, p.company")
                        company = comp_el.text.strip() if comp_el else "Careerjet Employer"
                        
                        loc_el = card.select_one(".location_compact, .locations, ul.location")
                        job_location = loc_el.text.strip() if loc_el else (location or "India")
                        
                        sal_el = card.select_one(".salary, ul.salary")
                        salary = sal_el.text.strip() if sal_el else "Not disclosed"
                        
                        desc_el = card.select_one(".desc, .job-description")
                        desc = desc_el.text.strip() if desc_el else ""
                        
                        details = f"Company: {company} | Location: {job_location} | Salary: {salary} | {desc}"
                        
                        if not any(j["Apply Link"] == apply_link for j in jobs_data):
                            jobs_data.append({
                                "Job Role": title,
                                "Company Name": company,
                                "Location": job_location,
                                "Date Posted": "Recent",
                                "Apply Link": apply_link,
                                "Company Link": "N/A",
                                "No. of Applicants": "N/A",
                                "Company / Job Details": details[:400] + "..." if len(details) > 400 else details,
                                "Source": "Careerjet"
                            })
                            added_on_page += 1
                            
                    print(f"[+] Careerjet: Extracted {added_on_page} matching jobs from page {page_idx}.")
                    if added_on_page == 0:
                        break
                        
                except Exception as page_err:
                    print(f"[!] Careerjet: Error on page {page_idx}: {page_err}")
                    break
                    
        except Exception as run_err:
            print(f"[!] Careerjet execution error: {run_err}")
        finally:
            await context.close()
            
    return jobs_data

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        role = sys.argv[1]
        loc = sys.argv[2]
    elif len(sys.argv) == 2:
        role = sys.argv[1]
        loc = ""
    else:
        role = "Python Developer"
        loc = "Bangalore"
        
    results = asyncio.run(scrape_careerjet_jobs(role, loc, max_pages=1, headless=True))
    print(f"\n[+] Scraper finished. Found {len(results)} jobs.")
    save_to_csv(results, "careerjet_jobs.csv")
