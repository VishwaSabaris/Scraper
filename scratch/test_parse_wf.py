import sys
sys.path.insert(0, '.')
from ddgs import DDGS
import re
from utils import get_company_website, is_role_match

def parse_wellfound_title(title_text):
    # Strip trailing "| Wellfound..."
    clean = re.sub(r'\s*\|\s*Wellfound.*$', '', title_text, flags=re.IGNORECASE).strip()
    
    comp_name = "N/A"
    location = "Remote / Various"
    role = clean
    
    if " at " in clean:
        parts = clean.split(" at ")
        role = parts[0].strip()
        rest = " at ".join(parts[1:]).strip()
        
        # Check for location bullet separator • or \u2022 or -
        if "•" in rest:
            subparts = [p.strip() for p in rest.split("•")]
            comp_name = subparts[0]
            if len(subparts) > 1:
                location = ", ".join(subparts[1:])
        elif " - " in rest:
            subparts = [p.strip() for p in rest.split(" - ")]
            comp_name = subparts[0]
            if len(subparts) > 1:
                location = ", ".join(subparts[1:])
        else:
            comp_name = rest
    elif " • " in clean:
        parts = [p.strip() for p in clean.split(" • ")]
        role = parts[0]
        if len(parts) > 1:
            comp_name = parts[1]
        if len(parts) > 2:
            location = ", ".join(parts[2:])
            
    return role, comp_name, location

with DDGS() as d:
    queries = [
        'site:wellfound.com/jobs "Lead Generation" Chennai',
        'site:wellfound.com/jobs "Lead Generation Executive"',
        'site:wellfound.com/jobs "Lead Generation" India',
        'site:wellfound.com/jobs "Lead Generation Specialist"',
        'site:wellfound.com/jobs "Business Development" Chennai',
        'site:wellfound.com/jobs "Demand Generation" India'
    ]
    seen_urls = set()
    all_extracted = []
    
    for q in queries:
        try:
            res = list(d.text(q, max_results=20))
            for r in res:
                url = r['href']
                if not url.startswith('https://wellfound.com/jobs/'):
                    continue
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                
                title = r['title']
                role, comp, loc = parse_wellfound_title(title)
                
                all_extracted.append({
                    "Job Role": role,
                    "Company Name": comp,
                    "Location": loc,
                    "Apply Link": url,
                    "Body": r['body']
                })
        except Exception as e:
            print("DDGS Error:", e)

print(f"Total unique wellfound jobs scraped: {len(all_extracted)}")
for item in all_extracted[:15]:
    print(f"Role: [{item['Job Role']}] | Comp: [{item['Company Name']}] | Loc: [{item['Location']}]")
    print(f"  URL: {item['Apply Link']}")
