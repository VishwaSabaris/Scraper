import asyncio
import sys
import re
import urllib.parse
import email.utils
import warnings
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from utils import save_to_csv, is_role_match, human_delay
from request_client import execute_async_request

# Suppress BS4 XML parsing warning when using HTML parser on XML feed
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

async def scrape_jobspresso_jobs(job_role, location="", max_pages=5):
    """
    Scrapes job listings from jobspresso.co using its paginated RSS feed.
    Returns a list of structured job dictionaries.
    """
    print(f"[*] Jobspresso: Fetching job listings for '{job_role}' in '{location or 'Any'}'...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    jobs_data = []
    
    for page in range(1, max_pages + 1):
        # Format search role for Jobspresso feed URL
        formatted_role = urllib.parse.quote(job_role)
        url = f"https://jobspresso.co/feed/?post_type=job_listing&s={formatted_role}&paged={page}"
        print(f"[*] Jobspresso: Navigating to page {page} ({url})...")
        
        try:
            res = await execute_async_request(url, method="GET", headers=headers, timeout=20)
            if not res or res.status_code != 200:
                # If page exceeds available pages, Jobspresso feed may return a non-200 status
                print(f"[-] Jobspresso: Received status code {res.status_code if res else 'None'} on page {page}. Stopping.")
                break
                
            soup = BeautifulSoup(res.content, "html.parser")
            items = soup.find_all("item")
            if not items:
                print(f"[-] Jobspresso: No items found on page {page}. Stopping.")
                break
                
            added_on_page = 0
            for item in items:
                title_el = item.find("title")
                if not title_el:
                    continue
                title = title_el.text.strip()
                
                # Check role match
                if not is_role_match(title, job_role):
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
                
                # Avoid duplicates
                if not any(j["Apply Link"] == apply_link for j in jobs_data):
                    jobs_data.append({
                        "Job Role": title,
                        "Company Name": company,
                        "Location": job_location,
                        "Date Posted": date_posted,
                        "Apply Link": apply_link,
                        "Company Link": "N/A",
                        "No. of Applicants": "N/A",
                        "Company / Job Details": details,
                        "Source": "Jobspresso"
                    })
                    added_on_page += 1
            
            print(f"[+] Jobspresso: Extracted {added_on_page} matching jobs from page {page}.")
            if added_on_page == 0:
                # If we parsed a page full of results and found no matching jobs, break early
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
