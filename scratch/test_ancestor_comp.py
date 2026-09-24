from bs4 import BeautifulSoup
import re

with open("scratch/scrolled_se.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

jls = soup.find_all('a', href=lambda h: h and re.search(r'/jobs/\d+', h))
print(f"Total job links: {len(jls)}")

for jl in jls:
    job_title = jl.text.strip()
    
    # Check if modern self-contained layout
    h3 = jl.find(['h3', 'h2'])
    comp_el = jl.find('p', class_=lambda c: c and 'font-semibold' in c)
    if h3 and h3.text.strip():
        job_title = h3.text.strip()
        
    comp_name = "YC Startup"
    comp_url = ""
    comp_batch = ""
    
    if comp_el and comp_el.text.strip():
        comp_name = comp_el.text.strip()
        
    if comp_name == "YC Startup":
        # Walk up parents until we find a company link
        p = jl.parent
        for _ in range(10):
            if not p: break
            # Find candidate company links in this ancestor
            candidates = []
            for a in p.find_all('a', href=lambda h: h and re.search(r'/companies/[a-zA-Z0-9_-]+$', h)):
                txt = a.text.strip()
                txt_l = txt.lower()
                if txt_l.startswith('see all') or txt_l.startswith('view all') or txt_l.startswith('view job') or txt_l == 'apply':
                    continue
                if len(txt) > 0:
                    candidates.append((a, txt, a['href']))
            if candidates:
                best_a, raw_text, href = candidates[0]
                # If there is one with hover:underline, prefer it
                for cand in candidates:
                    if 'hover:underline' in (cand[0].get('class') or []):
                        best_a, raw_text, href = cand
                        break
                comp_url = "https://www.workatastartup.com" + href if href.startswith('/') else href
                batch_match = re.search(r'\(([A-Z0-9]+)\)', raw_text)
                if batch_match:
                    comp_batch = batch_match.group(1)
                parts = re.split(r'[\u2022\u2013\u2014|\t\n\xb7]', raw_text)
                if parts:
                    comp_name = re.sub(r'\s*\([A-Z0-9]+\).*', '', parts[0]).strip()
                if not comp_name or len(comp_name) < 2 or 'see all' in comp_name.lower():
                    slug_match = re.search(r'/companies/([a-zA-Z0-9_-]+)', href)
                    if slug_match:
                        comp_name = slug_match.group(1).replace('-', ' ').title()
                break
            p = p.parent
            
    print(f"Role: {job_title:<45} | Company: {comp_name:<25} | Batch: {comp_batch:<5}")
