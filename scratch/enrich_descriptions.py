import os
import sys
import pandas as pd
from curl_cffi import requests as c_requests

def enrich_foundit():
    headers = {
        'authority': 'www.foundit.in',
        'accept': 'application/json, text/plain, */*',
        'referer': 'https://www.foundit.in/srp/results?query=DevOps&locations=Bangalore'
    }

    df = pd.read_csv('all_jobs_vvs.csv')
    foundit_map = {}

    print("[*] Fetching comprehensive job details from Foundit API...")
    for page in range(25):
        url = f'https://www.foundit.in/middleware/jobsearch?query=DevOps&locations=Bangalore&limit=20&start={page*20}&sort=1'
        try:
            res = c_requests.get(url, headers=headers, impersonate='chrome120', timeout=15)
            if res.status_code != 200:
                break
            items = res.json().get('jobSearchResponse', {}).get('data', [])
            if not items:
                break
            for it in items:
                title = it.get('title', '')
                comp = it.get('companyName') or it.get('company', {}).get('name') or ''
                
                # Extract experience
                min_exp = it.get('minimumExperience', {})
                max_exp = it.get('maximumExperience', {})
                min_y = min_exp.get('years', 0) if isinstance(min_exp, dict) else 0
                max_y = max_exp.get('years', 0) if isinstance(max_exp, dict) else 0
                exp = it.get('exp') or f"{min_y}-{max_y} Years"
                
                # Extract skills
                skills = it.get('skills', '')
                if isinstance(skills, list):
                    skills = ', '.join([s.get('text', '') if isinstance(s, dict) else str(s) for s in skills if s])
                
                sal = it.get('salary', '')
                funcs = it.get('functions', [])
                if isinstance(funcs, list):
                    funcs = ', '.join([f.get('text', '') if isinstance(f, dict) else str(f) for f in funcs if f])
                inds = it.get('industries', [])
                if isinstance(inds, list):
                    inds = ', '.join([i.get('text', '') if isinstance(i, dict) else str(i) for i in inds if i])
                
                parts = []
                if exp and exp != '0-0 Years': parts.append(f'Exp: {exp}')
                if sal and sal != '0-0 INR' and sal != 'Not disclosed': parts.append(f'Salary: {sal}')
                if skills: parts.append(f'Skills: {skills}')
                if inds and inds != 'Other': parts.append(f'Industry: {inds}')
                if funcs and funcs != 'Other': parts.append(f'Function: {funcs}')
                
                desc = ' | '.join(parts) if parts else f'Role: {title} at {comp}'
                app_link = it.get('redirectUrl') or it.get('applyUrl') or ''
                if app_link:
                    foundit_map[app_link] = desc
                foundit_map[(title.strip().lower(), str(comp).strip().lower())] = desc
        except Exception as e:
            print(f"[!] Error on page {page}: {e}")
            break

    print(f"[+] Loaded rich details for {len(foundit_map)} Foundit listings.")

    updated_count = 0
    for idx, row in df[df['Source'] == 'Foundit'].iterrows():
        link = str(row.get('Apply Link', ''))
        key = (str(row.get('Job Role', '')).strip().lower(), str(row.get('Company Name', '')).strip().lower())
        if link in foundit_map:
            df.at[idx, 'Company / Job Details'] = foundit_map[link]
            updated_count += 1
        elif key in foundit_map:
            df.at[idx, 'Company / Job Details'] = foundit_map[key]
            updated_count += 1
        else:
            # Clean fallback
            role_t = row.get('Job Role', '')
            comp_t = row.get('Company Name', '')
            loc_t = row.get('Location', '')
            df.at[idx, 'Company / Job Details'] = f"Role: {role_t} | Company: {comp_t} | Location: {loc_t}"

    print(f"[++++] Successfully enriched {updated_count} Foundit job listings with skills, experience, and responsibilities!")
    df.to_csv('all_jobs_vvs.csv', index=False)

if __name__ == '__main__':
    enrich_foundit()
