from bs4 import BeautifulSoup
import re

with open("scratch/yc_page.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

job_links = soup.find_all('a', href=lambda h: h and re.search(r'/jobs/\d+', h))
print(f"Total job links: {len(job_links)}")

parsed_jobs = []
for jl in job_links:
    job_title = jl.text.strip()
    job_href = jl['href']
    apply_link = "https://www.workatastartup.com" + job_href if job_href.startswith('/') else job_href
    
    # Now find the company name and company link from the enclosing card
    card = jl.parent
    for _ in range(8):
        if not card:
            break
        # Card container typically has hover:bg or border or is a distinct block containing the company link
        c_link = card.find('a', href=lambda h: h and re.search(r'/companies/[a-zA-Z0-9_-]+$', h) and 'See all' not in (card.find('a', href=h).text if card.find('a', href=h) else ''))
        # Let's find company link inside card that is NOT "See all"
        comp_candidate = None
        for a in card.find_all('a', href=lambda h: h and re.search(r'/companies/[a-zA-Z0-9_-]+$', h)):
            txt = a.text.strip()
            if not txt.startswith('See all') and not txt.startswith('View job') and len(txt) > 1:
                comp_candidate = a
                break
        if comp_candidate:
            break
        card = card.parent
        
    comp_name = "YC Startup"
    comp_url = "https://www.workatastartup.com"
    comp_tagline = ""
    comp_batch = ""
    
    if card and comp_candidate:
        raw_text = comp_candidate.text.strip()
        comp_url = "https://www.workatastartup.com" + comp_candidate['href'] if comp_candidate['href'].startswith('/') else comp_candidate['href']
        
        batch_match = re.search(r'\(([A-Z0-9]+)\)', raw_text)
        if batch_match:
            comp_batch = batch_match.group(1)
            
        parts = re.split(r'[\u2022\u2013\u2014|\t\n\xb7]', raw_text)
        if parts:
            comp_name = re.sub(r'\s*\([A-Z0-9]+\).*', '', parts[0]).strip()
            if len(parts) > 1:
                comp_tagline = parts[1].strip()

    # Location and details from card or job row
    card_text = card.text.strip() if card else ""
    
    parsed_jobs.append({
        "role": job_title,
        "company": comp_name,
        "batch": comp_batch,
        "tagline": comp_tagline,
        "apply_link": apply_link,
        "company_link": comp_url
    })

print(f"Successfully extracted {len(parsed_jobs)} jobs!")
for pj in parsed_jobs[:10]:
    print(f"Role: {pj['role']:<40} | Company: {pj['company']:<20} | Batch: {pj['batch']:<5} | URL: {pj['apply_link']}")
