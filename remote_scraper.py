import asyncio
import sys
import re
import json
import urllib.parse
import requests
from bs4 import BeautifulSoup
from utils import save_to_csv, is_role_match, human_delay
from request_client import execute_async_request

def matches_location(job_location, search_location):
    """
    Checks if job_location matches the requested search_location.
    Allows for country code synonyms (e.g. USA, US, United States) and global/remote roles.
    """
    if not search_location:
        return True
        
    jl_lower = job_location.lower()
    sl_lower = search_location.lower().strip()
    
    if sl_lower in jl_lower or "remote" in jl_lower or "global" in jl_lower:
        return True
        
    # USA synonyms
    usa_terms = {"usa", "us", "united states", "america"}
    if sl_lower in usa_terms:
        if any(term in jl_lower for term in usa_terms):
            return True
            
    # UK synonyms
    uk_terms = {"uk", "gbr", "united kingdom", "gb", "great britain"}
    if sl_lower in uk_terms:
        if any(term in jl_lower for term in uk_terms):
            return True
            
    # Canada synonyms
    ca_terms = {"ca", "can", "canada"}
    if sl_lower in ca_terms:
        if any(term in jl_lower for term in ca_terms):
            return True
            
    return False

async def scrape_remote_jobs(job_role, location="", max_pages=5, filter_params=None, **kwargs):
    """
    Scrapes job listings from remote.com using Next.js push-script extraction.
    Supports dynamic filter parameters and deep pagination.
    """
    fp = filter_params or {}
    effective_role = fp.get("query") or job_role
    effective_loc = fp.get("location") or location or ""
    
    print(f"[*] Remote.com: Fetching job listings for '{effective_role}' in '{effective_loc or 'Any'}'...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    jobs_data = []
    
    for page in range(1, max_pages + 1):
        params = {
            "query": effective_role,
            "page": page
        }
        if effective_loc:
            params["country"] = effective_loc
        for k in ["category", "job_type"]:
            if fp.get(k):
                params[k] = fp[k]
                
        url = f"https://remote.com/jobs/all?{urllib.parse.urlencode(params)}"
        print(f"[*] Remote.com: Navigating to page {page} ({url})...")
        
        try:
            res = await execute_async_request(url, method="GET", headers=headers, timeout=20)
            if not res or res.status_code != 200:
                print(f"[!] Remote.com: Received status code {res.status_code if res else 'None'} on page {page}. Stopping.")
                break
                
            soup = BeautifulSoup(res.text, "html.parser")
            found_script = False
            added_on_page = 0
            
            for script in soup.find_all("script"):
                if script.string and "jobsData" in script.string:
                    found_script = True
                    content = script.string
                    matches = re.findall(r'self\.__next_f\.push\(\[\d+,\"(.*)\"\]\)', content)
                    
                    for m in matches:
                        # Unescape Next.js push chunk
                        try:
                            decoded = json.loads(f'"{m}"')
                        except Exception:
                            decoded = m.replace('\\"', '"').replace('\\\\', '\\')
                        idx = decoded.find('"jobsData":')
                        if idx == -1:
                            continue
                            
                        # Trace from the curly brace preceding "jobsData"
                        brace_idx = decoded.rfind('{', 0, idx)
                        if brace_idx == -1:
                            continue
                            
                        sub = decoded[brace_idx:]
                        brace_count = 0
                        json_str = ""
                        for char in sub:
                            json_str += char
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    break
                                    
                        try:
                            data = json.loads(json_str)
                            jd = data.get("jobsData", {})
                            jobs_list = jd.get("jobs", [])
                            if not jobs_list:
                                continue
                                
                            for item in jobs_list:
                                title = item.get("title", "N/A")
                                
                                # Role match filter
                                if not is_role_match(title, job_role):
                                    continue
                                    
                                comp_info = item.get("companyProfile") or {}
                                company = comp_info.get("name", "Remote.com Employer")
                                comp_url = comp_info.get("websiteUrl") or "N/A"
                                
                                # Parse location
                                hiring_loc = item.get("hiringLocation") or {}
                                loc_type = hiring_loc.get("type", "")
                                if loc_type == "global":
                                    job_location = "Global / Remote"
                                elif loc_type == "location":
                                    included = hiring_loc.get("includedLocations", []) or []
                                    loc_names = []
                                    for loc in included:
                                        val = loc.get("value", {})
                                        if val and isinstance(val, dict):
                                            name = val.get("name")
                                            if name:
                                                loc_names.append(name)
                                    job_location = ", ".join(loc_names) if loc_names else "Remote"
                                else:
                                    job_location = "Remote"
                                    
                                # Location filtering
                                if not matches_location(job_location, location):
                                    continue
                                    
                                # Parse Date Posted
                                pub_at = item.get("publishedAt") or item.get("insertedAt") or ""
                                date_posted = "N/A"
                                if pub_at:
                                    date_posted = pub_at.split("T")[0].split("Z")[0]
                                    
                                # Apply link
                                apply_link = item.get("applyUrl")
                                comp_slug = comp_info.get("slug", "")
                                job_slug = item.get("slug", "")
                                if not apply_link and comp_slug and job_slug:
                                    apply_link = f"https://remote.com/jobs/{comp_slug}/{job_slug}"
                                elif not apply_link:
                                    apply_link = "N/A"
                                    
                                # No. of Applicants
                                apps = item.get("totalApplications")
                                applicants = str(apps) if apps is not None else "N/A"
                                
                                # Compile details
                                workplace = item.get("workplaceLocation", {}).get("type", "remote")
                                emp_type = item.get("employmentType", "N/A")
                                seniority_list = item.get("seniority", [])
                                seniority_str = ", ".join(seniority_list) if seniority_list else "N/A"
                                
                                comp = item.get("compensation") or {}
                                if comp:
                                    min_sal = comp.get("minimum")
                                    max_sal = comp.get("maximum")
                                    curr = comp.get("currency", {}).get("code", "")
                                    freq = comp.get("frequency", "")
                                    if min_sal is not None and max_sal is not None:
                                        salary_str = f"{min_sal} - {max_sal} {curr} ({freq})"
                                    elif min_sal is not None:
                                        salary_str = f"From {min_sal} {curr} ({freq})"
                                    else:
                                        salary_str = "N/A"
                                else:
                                    salary_str = "N/A"
                                    
                                details = f"Workplace: {workplace.capitalize()} | Type: {emp_type.capitalize()} | Seniority: {seniority_str.capitalize()} | Salary: {salary_str}"
                                
                                if not any(j["Apply Link"] == apply_link for j in jobs_data):
                                    jobs_data.append({
                                        "Job Role": title,
                                        "Company Name": company,
                                        "Location": job_location,
                                        "Date Posted": date_posted,
                                        "Apply Link": apply_link,
                                        "Company Link": comp_url,
                                        "No. of Applicants": applicants,
                                        "Company / Job Details": details,
                                        "Source": "Remote.com"
                                    })
                                    added_on_page += 1
                                    
                        except Exception as json_err:
                            print(f"[!] Remote.com: JSON decode error in script on page {page}: {json_err}")
                            
            print(f"[+] Remote.com: Extracted {added_on_page} matching jobs from page {page}.")
            
            # If no script containing jobsData was found on the page, stop paginating
            if not found_script:
                print(f"[-] Remote.com: jobsData script not found on page {page}. Stopping.")
                break
                
            # Add human delay between requests
            await human_delay(1.5, 3.0)
            
        except Exception as err:
            print(f"[!] Remote.com: Error parsing page {page}: {err}")
            break
            
    print(f"[+] Remote.com: Scrape completed. Extracted {len(jobs_data)} jobs in total.")
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
        
    results = asyncio.run(scrape_remote_jobs(role, loc))
    print(f"\n[+] Remote Scraper finished. Total results: {len(results)}")
    save_to_csv(results, "remote_jobs.csv")
