import sys, os
sys.path.insert(0, os.path.abspath("."))
import re
from bs4 import BeautifulSoup
from utils import is_role_match, normalize_date_posted, get_company_website

with open("scratch/yc_page.html", "r", encoding="utf-8") as f:
    html_content = f.read()

def parse_workatastartup_html(html_content, job_role_filter="", work_mode_filter=""):
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []
    seen_apply_links = set()
    
    job_links = soup.find_all('a', href=lambda h: h and re.search(r'/jobs/\d+', h))
    
    for jl in job_links:
        job_title = jl.text.strip()
        j_href = jl['href']
        apply_link = "https://www.workatastartup.com" + j_href if j_href.startswith('/') else j_href
        
        if not job_title or apply_link in seen_apply_links:
            continue
            
        if job_role_filter and not is_role_match(job_title, job_role_filter):
            continue
            
        seen_apply_links.add(apply_link)
        
        card = jl.parent
        for _ in range(8):
            if not card:
                break
            classes = " ".join(card.get('class') or [])
            if ('border' in classes and ('rounded' in classes or 'p-3' in classes or 'p-4' in classes)) or len(card.find_all('a')) >= 3:
                break
            card = card.parent
            
        comp_name = "YC Startup"
        comp_tagline = ""
        comp_batch = ""
        comp_url = ""
        
        if card:
            comp_candidates = []
            for a in card.find_all('a', href=lambda h: h and re.search(r'/companies/[a-zA-Z0-9_-]+$', h)):
                href = a['href']
                if href.endswith('/companies'):
                    continue
                txt = " ".join(a.text.split())
                txt_lower = txt.lower()
                if txt_lower.startswith('see all') or txt_lower.startswith('view all') or txt_lower.startswith('view job') or txt_lower == 'apply':
                    continue
                if len(txt) > 0:
                    comp_candidates.append((a, txt, href))
                    
            if comp_candidates:
                best_link, raw_comp_text, comp_href = comp_candidates[0]
                for cand in comp_candidates:
                    if 'hover:underline' in (cand[0].get('class') or []):
                        best_link, raw_comp_text, comp_href = cand
                        break
                        
                comp_url = "https://www.workatastartup.com" + comp_href if comp_href.startswith('/') else comp_href
                
                batch_match = re.search(r'\(([A-Z0-9]+)\)', raw_comp_text)
                if batch_match:
                    comp_batch = batch_match.group(1)
                    
                parts = re.split(r'[\u2022\u2013\u2014|\t\n\xb7]', raw_comp_text)
                if parts:
                    comp_name = re.sub(r'\s*\([A-Z0-9]+\).*', '', parts[0]).strip()
                    if len(parts) > 1:
                        comp_tagline = parts[1].strip()
                        
                if not comp_name or len(comp_name) < 2 or 'see all' in comp_name.lower():
                    slug_match = re.search(r'/companies/([a-zA-Z0-9_-]+)', comp_href)
                    if slug_match:
                        comp_name = slug_match.group(1).replace('-', ' ').title()
            else:
                any_comp = card.find('a', href=lambda h: h and '/companies/' in h)
                if any_comp and any_comp.get('href'):
                    slug_match = re.search(r'/companies/([a-zA-Z0-9_-]+)', any_comp['href'])
                    if slug_match:
                        comp_name = slug_match.group(1).replace('-', ' ').title()
                        comp_url = "https://www.workatastartup.com" + any_comp['href'] if any_comp['href'].startswith('/') else any_comp['href']

        card_text = " ".join(card.text.split()) if card else ""
        
        j_row = jl.parent
        for _ in range(4):
            if j_row and j_row.name in ['div', 'li', 'tr'] and len(j_row.find_all(['span', 'div', 'a'])) > 2:
                break
            if j_row:
                j_row = j_row.parent
        r_text = " ".join(j_row.text.split()) if j_row else card_text
        
        salary_str = "N/A"
        sal_match = re.search(r'\$\d+K?\s*-\s*\$\d+K?|\$\d+,\d+\s*-\s*\$\d+,\d+|[£€]\d+K?\s*-\s*[£€]\d+K?|₹\d+[MK]?\s*-\s*₹\d+[MK]?', r_text, re.IGNORECASE)
        if sal_match:
            salary_str = sal_match.group(0)
            
        loc_str = "Remote / Various"
        loc_tokens = []
        for token in re.split(r'[\n\t•|\xb7/]', r_text):
            t_clean = token.strip()
            if any(k in t_clean for k in ['London', 'United Kingdom', 'UK', 'San Francisco', 'Mountain View', 'Austin', 'New York', 'India', 'IN', 'Remote', 'CA', 'NY', 'US', 'GB']):
                if t_clean not in loc_tokens and len(t_clean) < 60 and not any(ch in t_clean for ch in ['$','£','€','₹','%']):
                    loc_tokens.append(t_clean)
        if loc_tokens:
            loc_str = " / ".join(loc_tokens[:2])
            
        if work_mode_filter and "remote" in work_mode_filter.lower():
            if "remote" not in loc_str.lower() and "remote" not in r_text.lower() and "remote" not in card_text.lower():
                loc_str = f"{loc_str} (Remote)" if loc_str and loc_str != "Remote / Various" else "Remote"
                
        comp_clean = comp_name if (comp_name and comp_name != "N/A") else "YC Verified Startup"
        loc_clean = loc_str if (loc_str and loc_str != "N/A") else "Remote / Worldwide"
        
        results.append({
            "Job Role": job_title,
            "Company Name": comp_clean,
            "Location": loc_clean,
            "Apply Link": apply_link,
            "Company Link": comp_url or "https://www.workatastartup.com",
            "Salary": salary_str,
            "Batch": comp_batch
        })
        
    return results

res = parse_workatastartup_html(html_content, job_role_filter="Python", work_mode_filter="remote")
print(f"Extracted {len(res)} matching jobs:")
for r in res:
    print(f"Role: {r['Job Role']:<45} | Company: {r['Company Name']:<20} | Loc: {r['Location']:<30} | {r['Apply Link']}")
