import asyncio
import os
import sys
import re
import math
import urllib.parse
import requests
from bs4 import BeautifulSoup
from utils import save_to_csv, is_role_match, normalize_date_posted, get_company_website
from request_client import execute_async_request

async def scrape_reed_jobs(job_role, location="", max_pages=None, strict_role_match=True, filter_params=None, **kwargs):
    """
    Scrapes maximum job listings from Reed.co.uk for a given job role and location.
    Supports dynamic filter parameters and deep pagination.
    """
    fp = filter_params or {}
    effective_role = fp.get("keywords") or job_role
    effective_loc = fp.get("location") or location or ""
    
    print(f"[*] Reed.co.uk: Scraping maximum job listings for '{effective_role}' in '{effective_loc or 'Any'}'...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    session = requests.Session()
    session.headers.update(headers)

    query_params = {'keywords': effective_role.strip()}
    if effective_loc and effective_loc.strip():
        query_params['location'] = effective_loc.strip()
    for k, v in fp.items():
        if k not in ["role", "location", "keywords"]:
            query_params[k] = v

    base_url = "https://www.reed.co.uk/jobs?" + urllib.parse.urlencode(query_params)
    print(f"[*] Reed.co.uk: Navigating to search URL: {base_url}")

    async def fetch_page_async(url):
        try:
            return await execute_async_request(url, method="GET", headers=headers, session=session)
        except Exception as err:
            print(f"[!] Error requesting {url}: {err}")
            return None

    first_resp = await fetch_page_async(base_url)
    if not first_resp or first_resp.status_code != 200:
        print(f"[!] Reed.co.uk: Received status code {first_resp.status_code if first_resp else 'None'} for search query.")
        return []

    first_soup = BeautifulSoup(first_resp.text, 'html.parser')

    # Detect total count from H1 header
    total_count = None
    h1 = first_soup.find('h1')
    if h1:
        h1_text = h1.text.strip()
        print(f"[*] Reed.co.uk Header: '{h1_text}'")
        match = re.search(r'([\d,]+)\s+.*job', h1_text, re.IGNORECASE)
        if match:
            total_count = int(match.group(1).replace(',', ''))
            print(f"[+] Reed.co.uk: Site reports {total_count:,} total jobs available for this search.")

    if total_count and total_count > 0:
        total_pages = math.ceil(total_count / 25)
    else:
        total_pages = 100  # Default ceiling

    # Cap total pages to max 100 as Reed limits search results
    total_pages = min(total_pages, 100)

    if max_pages is not None:
        target_pages = min(total_pages, int(max_pages))
    else:
        target_pages = total_pages

    print(f"[*] Reed.co.uk: Target pagination limit set to {target_pages} pages (~{target_pages * 25} job cards max).")

    jobs_data = []
    seen_links = set()

    for page in range(1, target_pages + 1):
        page_url = f"{base_url}&pageno={page}"
        print(f"[*] Reed.co.uk [Page {page}/{target_pages}]: Fetching {page_url}...", flush=True)

        if page > 1:
            resp = await fetch_page_async(page_url)
            if not resp:
                continue
            if resp.status_code == 404:
                print(f"[-] Reed.co.uk: Reached 404 page end at page {page}. Stopping.")
                break
            if resp.status_code != 200:
                print(f"[!] Reed.co.uk: HTTP {resp.status_code} on page {page}. Skipping.")
                continue
            soup = BeautifulSoup(resp.text, 'html.parser')
        else:
            soup = first_soup

        cards = soup.select('article[class*="job-card"]')
        if not cards:
            print(f"[-] Reed.co.uk: No job cards found on page {page}. Ending pagination loop.")
            break

        scraped_on_page = 0
        for card in cards:
            title_el = card.select_one('a[data-qa="job-card-title"]') or card.select_one('a[data-element="job_title"]')
            if not title_el:
                continue

            title = title_el.text.strip()
            if not title:
                continue

            href = title_el.get('href', '')
            if href.startswith('/'):
                apply_link = "https://www.reed.co.uk" + href
            else:
                apply_link = href

            if apply_link in seen_links:
                continue
            seen_links.add(apply_link)

            # Role match filtering
            if strict_role_match and not is_role_match(title, job_role):
                continue

            # Company name & Recruiter link
            company = "Reed Employer"
            company_link = "N/A"
            recruiter_el = card.select_one('a[data-element="recruiter"]')
            if recruiter_el:
                company = recruiter_el.text.strip()
                r_href = recruiter_el.get('href', '')
                if r_href.startswith('/'):
                    company_link = "https://www.reed.co.uk" + r_href
                else:
                    company_link = r_href

            # Posted date
            posted_date = "N/A"
            posted_by_el = card.select_one('div[data-qa="job-posted-by"]')
            if posted_by_el:
                raw_text = posted_by_el.text.strip()
                if 'by' in raw_text:
                    posted_date = raw_text.split('by')[0].strip()
                else:
                    posted_date = raw_text

            # Location
            location_val = location if location else "United Kingdom"
            loc_el = card.select_one('li[data-qa="job-metadata-location"]')
            if loc_el:
                location_val = loc_el.text.strip()

            # Salary
            salary_val = "N/A"
            salary_el = card.select_one('li[data-qa="job-metadata-salary"]')
            if salary_el:
                salary_val = salary_el.text.strip()

            # Contract / Job Type
            metadata_items = card.select('ul[data-qa="job-metadata"] li')
            job_types = []
            for item in metadata_items:
                if item != loc_el and item != salary_el:
                    item_text = item.text.strip()
                    if item_text:
                        job_types.append(item_text)

            job_type_str = ", ".join(job_types) if job_types else "N/A"

            # Badges (e.g. Easy Apply, Featured)
            badges = [b.text.strip() for b in card.select('.badge') if b.text.strip()]
            badge_str = f" | Badges: {', '.join(badges)}" if badges else ""

            comp_clean = company if (company and company != "N/A") else "Reed Verified Employer"
            loc_clean = location_val if (location_val and location_val != "N/A") else (location or "London, UK / Remote")
            job_type_str = ", ".join(job_types) if job_types else "Full-time"
            details = f"Company: {comp_clean} | Salary: {salary_val} | Type: {job_type_str}{badge_str}"
            final_comp_url = company_link if (company_link and company_link != "N/A" and company_link.startswith("http")) else get_company_website(comp_clean, fallback_portal_url="https://www.reed.co.uk")

            job_obj = {
                "Job Role": title,
                "Company Name": comp_clean,
                "Location": loc_clean,
                "Date Posted": normalize_date_posted(posted_date),
                "Apply Link": apply_link,
                "Company Link": final_comp_url,
                "No. of Applicants": "Actively Hiring",
                "Company / Job Details": details,
                "Source": "Reed.co.uk"
            }
            jobs_data.append(job_obj)
            scraped_on_page += 1

        print(f"    [+] Page {page}: Extracted {scraped_on_page} relevant job listings. (Total so far: {len(jobs_data)})", flush=True)
        await asyncio.sleep(0.2)

    print(f"\n[++++] Reed.co.uk: Extraction complete! Successfully scraped {len(jobs_data)} job listings across {page} pages.")
    save_to_csv(jobs_data, filename="reed_jobs.csv")
    return jobs_data

async def main():
    if len(sys.argv) >= 2:
        role_input = sys.argv[1]
        location_input = sys.argv[2] if len(sys.argv) >= 3 else ""
        max_pages_input = int(sys.argv[3]) if len(sys.argv) >= 4 else None
    else:
        role_input = input("Enter Job Role (e.g. Python Developer): ").strip()
        location_input = input("Enter Location (optional, e.g. London): ").strip()
        pages_str = input("Enter max pages to scrape (press Enter for ALL available pages): ").strip()
        max_pages_input = int(pages_str) if pages_str.isdigit() else None

    await scrape_reed_jobs(role_input, location_input, max_pages=max_pages_input)

if __name__ == '__main__':
    asyncio.run(main())
