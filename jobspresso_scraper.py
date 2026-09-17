import asyncio
import sys
import re
import urllib.parse
import email.utils
import warnings
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from utils import save_to_csv, is_role_match, human_delay, normalize_date_posted, get_company_website
from request_client import execute_async_request

# Suppress BS4 XML parsing warning when using HTML parser on XML feed
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

from curl_cffi import requests as c_requests

async def scrape_jobspresso_jobs(job_role, location="", max_pages=5, filter_params=None, **kwargs):
    """
    Scrapes job listings from jobspresso.co using its paginated RSS feed with multi-term recall.
    Supports dynamic filter parameters and deep pagination.
    """
    fp = filter_params or {}
    effective_role = fp.get("s") or job_role
    
    print(f"[*] Jobspresso: Fetching job listings for '{effective_role}' in '{location or 'Any'}'...")
    
    search_terms = [effective_role]
    if " " in effective_role:
        for t in effective_role.split():
            if len(t) > 3 and t.lower() not in ["with", "from", "jobs", "senior", "junior"]:
                search_terms.append(t)
                
    jobs_data = []
    seen_links = set()
    
    for term in search_terms:
        if len(jobs_data) >= max_pages * 20:
            break
            
        for page in range(1, max_pages + 1):
            formatted_term = urllib.parse.quote(term)
            url = f"https://jobspresso.co/feed/?post_type=job_listing&s={formatted_term}&paged={page}"
            print(f"[*] Jobspresso: Querying '{term}' page {page} ({url})...")
            
            try:
                res = await asyncio.to_thread(
                    c_requests.get,
                    url,
                    impersonate="chrome120",
                    timeout=15
                )
                if not res or res.status_code != 200:
                    break
                    
                soup = BeautifulSoup(res.content, "html.parser")
                items = soup.find_all("item")
                if not items:
                    break
                    
                added_on_page = 0
                for item in items:
                    title_el = item.find("title")
                    if not title_el:
                        continue
                    title = title_el.text.strip()
                    
                    # Check role match
                    if not is_role_match(title, job_role) and not any(t.lower() in title.lower() for t in job_role.split() if len(t) > 2):
                        continue
                
                    # Extract creator tag which contains "Company Name<br>⚲ Location"
                    creator_el = item.find("dc:creator") or item.find("creator")
                    if creator_el:
                        creator_text = creator_el.text.strip()
                        # Split by <br> or <br/>
                        parts = re.split(r'<br\s*/?>', creator_text, flags=re.IGNORECASE)
                        company = parts[0].strip() if len(parts) > 0 else "Jobspresso Employer"
                        
                        if len(parts) > 1:
                            # Clean location text
                            loc_raw = parts[1].strip()
                            # Remove ⚲ symbol and spaces
                            loc_clean = loc_raw.replace("⚲", "").replace("&nbsp;", " ").replace("\xa0", " ").strip()
                            job_location = loc_clean or "Remote"
                        else:
                            job_location = "Remote"
                    else:
                        company = "Jobspresso Employer"
                        job_location = "Remote"
                    
                    # Location filtering
                    if location and location.lower() not in job_location.lower() and "remote" not in job_location.lower():
                        continue
                    
                    # Date posted conversion
                    pub_date_el = item.find("pubdate") or item.find("pubDate")
                    date_posted = "N/A"
                    if pub_date_el:
                        try:
                            dt = email.utils.parsedate_to_datetime(pub_date_el.text)
                            date_posted = dt.strftime("%Y-%m-%d")
                        except Exception:
                            pass
                    
                    # Apply link
                    link_el = item.find("link")
                    apply_link = link_el.text.strip() if link_el else "N/A"
                    
                    # Job Details parsing
                    desc_el = item.find("description")
                    details = "N/A"
                    if desc_el:
                        desc_soup = BeautifulSoup(desc_el.text, "html.parser")
                        details_text = desc_soup.get_text(separator=" ").strip()
                        # Clean whitespace and slice
                        details = re.sub(r'\s+', ' ', details_text)
                        if len(details) > 300:
                            details = details[:300] + "..."
                    
                    comp_clean = company if (company and company != "N/A") else "Jobspresso Verified Employer"
                    loc_clean = job_location if (job_location and job_location != "N/A") else (location or "Remote / Worldwide")
                    if details == "N/A" or not details:
                        details = f"Role: {title} | Company: {comp_clean} | Location: {loc_clean} | Source: Jobspresso"

                    # Avoid duplicates
                    if not any(j["Apply Link"] == apply_link for j in jobs_data):
                        jobs_data.append({
                            "Job Role": title,
                            "Company Name": comp_clean,
                            "Location": loc_clean,
                            "Date Posted": normalize_date_posted(date_posted),
                            "Apply Link": apply_link,
                            "Company Link": get_company_website(comp_clean, fallback_portal_url="https://jobspresso.co"),
                            "No. of Applicants": "Actively Hiring",
                            "Company / Job Details": details,
                            "Source": "Jobspresso"
                        })
                        added_on_page += 1
                
                print(f"[+] Jobspresso: Extracted {added_on_page} matching jobs from page {page}.")
                if added_on_page == 0:
                    pass
                    
                # Add brief human delay between page requests
                await human_delay(1.5, 3.0)
                
            except Exception as err:
                print(f"[!] Jobspresso: Error parsing page {page}: {err}")
                break
            
    print(f"[+] Jobspresso: Scrape completed. Extracted {len(jobs_data)} jobs in total.")
    return jobs_data

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        role = sys.argv[1]
        loc = sys.argv[2]
    elif len(sys.argv) == 2:
        role = sys.argv[1]
        loc = ""
    else:
        role = input("Enter Job Role: ").strip()
        loc = input("Enter Location: ").strip()
        
    results = asyncio.run(scrape_jobspresso_jobs(role, loc))
    print(f"\n[+] Jobspresso Scraper finished. Total results: {len(results)}")
    save_to_csv(results, "jobspresso_jobs.csv")
