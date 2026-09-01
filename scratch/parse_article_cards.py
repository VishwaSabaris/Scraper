import asyncio
import os
import sys
sys.path.append(os.path.abspath("."))
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils import CHROMIUM_STEALTH_ARGS, is_role_match

async def test_extract_articles():
    user_dir = os.path.abspath("./ziprecruiter_session")
    os.makedirs(user_dir, exist_ok=True)
    
    url = "https://www.ziprecruiter.com/jobs-search?search=Software+Developer&location=London"
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_dir,
            headless=False,
            channel="chrome",
            args=CHROMIUM_STEALTH_ARGS,
            viewport={'width': 1366, 'height': 768}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        await page.goto(url, timeout=40000)
        await asyncio.sleep(5)
        
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        articles = soup.find_all("article")
        print(f"Total articles found: {len(articles)}")
        
        extracted = []
        for idx, art in enumerate(articles):
            # 1. Title
            h2 = art.find(["h2", "h3"])
            title = h2.get_text(strip=True) if h2 else "N/A"
            if title == "N/A" or not title:
                continue
                
            # 2. Company
            comp_el = art.find(attrs={"data-testid": "job-card-company"})
            company = comp_el.get_text(strip=True) if comp_el else "ZipRecruiter Employer"
            comp_href = comp_el.get("href", "") if comp_el else ""
            company_link = f"https://www.ziprecruiter.com{comp_href}" if comp_href.startswith("/") else (comp_href or "N/A")
            
            # 3. Location
            loc_el = art.find(attrs={"data-testid": "job-card-location"})
            job_location = loc_el.get_text(strip=True) if loc_el else "London"
            
            # 4. Apply Link / Job Key
            # Check article id or links
            art_id = art.get("id", "")
            job_key = art_id.replace("job-card-", "") if "job-card-" in art_id else art_id
            
            # Find links inside article
            a_tags = art.find_all("a", href=True)
            apply_link = "N/A"
            for a in a_tags:
                href = a.get("href", "")
                if "lk=" in href or "/job/" in href:
                    apply_link = f"https://www.ziprecruiter.com{href}" if href.startswith("/") else href
                    break
                    
            if apply_link == "N/A" and job_key:
                apply_link = f"https://www.ziprecruiter.com/jobs-search?search=Software+Developer&location=London&lk={job_key}"
            elif apply_link == "N/A" and a_tags:
                href = a_tags[0].get("href", "")
                apply_link = f"https://www.ziprecruiter.com{href}" if href.startswith("/") else href
                
            # 5. Date posted / salary / details
            salary_el = art.find(attrs={"data-testid": lambda t: t and "salary" in t}) or art.find(class_=lambda c: c and "salary" in c)
            salary_str = salary_el.get_text(strip=True) if salary_el else ""
            
            p_text = art.get_text(separator=' ', strip=True)
            details = f"Details: {p_text[:200]}..."
            if salary_str:
                details = f"Salary: {salary_str} | {details}"
                
            date_posted = "N/A"
            for t in ["posted", "ago", "today", "yesterday", "just"]:
                for term in p_text.split():
                    if t in term.lower():
                        date_posted = term
                        break
                        
            extracted.append({
                "title": title,
                "company": company,
                "location": job_location,
                "apply_link": apply_link,
                "company_link": company_link,
                "date_posted": date_posted,
                "details": details
            })
            
        print(f"\nSuccessfully extracted {len(extracted)} structured jobs!")
        for j in extracted[:5]:
            print(f" - {j['title']} | {j['company']} | {j['location']} | Link: {j['apply_link'][:60]}")
            
        await context.close()

if __name__ == "__main__":
    asyncio.run(test_extract_articles())
