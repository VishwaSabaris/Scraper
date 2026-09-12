from bs4 import BeautifulSoup
import re

with open("./scratch/apna_sample.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

jobs = []
for a in soup.find_all("a", href=re.compile(r"^/job/")):
    href = a.get("href")
    full_url = f"https://apna.co{href}"
    
    # Check if already added
    if any(j["link"] == full_url for j in jobs):
        continue
        
    # Get container
    container = a.find_parent("section") or a.find_parent("div")
    if not container:
        continue
        
    # Find title
    title_el = a.find(["h2", "h3", "h4", "p", "span"]) or a
    title = title_el.text.strip() if title_el else ""
    
    # Extract strings from card
    strings = [s.strip() for s in container.stripped_strings if s.strip()]
    
    # If title is empty or generic, use first string
    if not title and strings:
        title = strings[0]
        
    company = "Apna Employer"
    location = "India"
    salary = "Not disclosed"
    
    # Look for known patterns
    if len(strings) >= 2:
        # Check if first is title, second is company
        if strings[0] == title and len(strings) > 1:
            company = strings[1]
        elif len(strings) > 2:
            company = strings[1]
            
    # Look for location keywords
    for s in strings:
        if any(c in s.lower() for c in ["bengaluru", "bangalore", "mumbai", "hyderabad", "delhi", "pune", "chennai", "noida", "gurgaon", "remote", "work from home"]):
            location = s
            break
            
    # Look for salary
    for s in strings:
        if "\u20b9" in s or "inr" in s.lower() or "lpa" in s.lower() or "month" in s.lower():
            salary = s
            break

    jobs.append({
        "title": title,
        "company": company,
        "location": location,
        "salary": salary,
        "link": full_url
    })

print(f"Extracted {len(jobs)} Apna jobs!")
for idx, j in enumerate(jobs[:5]):
    print(f"Job {idx}: {j['title']} | {j['company']} | {j['location']} | {j['salary']}")
