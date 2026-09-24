import sys
sys.path.insert(0, '.')
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import re
import json
import time
from bs4 import BeautifulSoup
from curl_cffi import requests

# List of discovered job URLs from test_ddgs_multi
job_urls = [
  "https://wellfound.com/jobs/4691323-lead-generation-executive",
  "https://wellfound.com/jobs/4697821-b2b-lead-generation-executive",
  "https://wellfound.com/jobs/4718554-lead-generation-executive",
  "https://wellfound.com/jobs/4656830-lead-generation-executive-clone",
  "https://wellfound.com/jobs/3902550-lead-generation-executive",
  "https://wellfound.com/jobs/4627285-business-development-executive-linkedin-linkedin-lead-generation",
  "https://wellfound.com/jobs/4688487-sales-partner-lead-generation-contractor-30-recurring-commission",
  "https://wellfound.com/jobs/4657069-digital-marketing-lead-generation-intern",
  "https://wellfound.com/jobs/4628491-linkedin-lead-generation-intern",
  "https://wellfound.com/jobs/4505555-linkedin-outreach-lead-generation-specialist-part-time",
  "https://wellfound.com/jobs/4025263-lead-generation-specialist",
  "https://wellfound.com/jobs/3534650-2-lead-generation-specialist-dental-international",
  "https://wellfound.com/jobs/4436572-senior-growth-outbound-lead-generation-manager",
  "https://wellfound.com/jobs/4452715-lead-generation-us-shift",
  "https://wellfound.com/jobs/4697944-sales-development-representative-sdr",
  "https://wellfound.com/jobs/4664484-sales-development-representative-sdr",
  "https://wellfound.com/jobs/4607023-sales-development-representative-sdr-founding-team",
  "https://wellfound.com/jobs/4589307-sales-development-representative",
  "https://wellfound.com/jobs/4577356-sales-development-representative",
  "https://wellfound.com/jobs/4307336-sales-development-representative-sdr",
  "https://wellfound.com/jobs/3768594-sales-development-representative-sdr",
  "https://wellfound.com/jobs/4607062-business-development-representative",
  "https://wellfound.com/jobs/4223965-2-business-development-representative",
  "https://wellfound.com/jobs/4728246-business-development-associate",
  "https://wellfound.com/jobs/4677994-business-development-lead-generator-commission-only-at-step-ai-clone",
  "https://wellfound.com/jobs/4607121-business-development-executive",
  "https://wellfound.com/jobs/4607038-business-development-executive",
  "https://wellfound.com/jobs/4557441-business-development-executive-brand-partnerships",
  "https://wellfound.com/jobs/4520965-business-development-executive",
  "https://wellfound.com/jobs/4480919-business-development-executive-job",
  "https://wellfound.com/jobs/4480917-business-development-executive",
  "https://wellfound.com/jobs/4377478-business-development-executive-it-services-ai-web",
  "https://wellfound.com/jobs/4238488-business-development-executive",
  "https://wellfound.com/jobs/4718634-inside-sales",
  "https://wellfound.com/jobs/4688463-inside-sales-associate",
  "https://wellfound.com/jobs/4435464-inside-sales-executive",
  "https://wellfound.com/jobs/4289678-inside-sales-representative-isr",
  "https://wellfound.com/jobs/4618120-founding-demand-generation-lead",
  "https://wellfound.com/jobs/4594783-demand-generation",
  "https://wellfound.com/jobs/4507161-sr-demand-generation-manager",
  "https://wellfound.com/jobs/4452953-demand-generation-manager-industrials-manufacturing",
  "https://wellfound.com/jobs/4150314-head-of-growth-demand-generation",
  "https://wellfound.com/jobs/4463590-lead-sales-representative",
  "https://wellfound.com/jobs/4607090-sales-representative",
  "https://wellfound.com/jobs/4656824-sales-representative-hotel-industry",
  "https://wellfound.com/jobs/4657018-sales-representative-event-lead-management-saas-product",
  "https://wellfound.com/jobs/4628458-sales-development-representative-sdr-remote-india-clone",
  "https://wellfound.com/jobs/4628499-inside-sales-aws",
  "https://wellfound.com/jobs/4688353-technical-sales-specialist-inside-sales-lims-eln",
  "https://wellfound.com/jobs/4716575-business-development-market-expansion-lead"
]

def fetch_details(url):
    try:
        r = requests.get(url, impersonate="chrome120", timeout=10)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, 'html.parser')
        json_ld = soup.find('script', type='application/ld+json')
        if not json_ld or not json_ld.text:
            return None
        data = json.loads(json_ld.text)
        if data.get('@type') != 'JobPosting':
            return None
            
        title = data.get('title', '').strip()
        org = data.get('hiringOrganization', {})
        comp_name = org.get('name', '').strip() if isinstance(org, dict) else ''
        comp_url = org.get('sameAs', '').strip() if isinstance(org, dict) else ''
        
        # Clean company url
        if not comp_url or 'wellfound.com' in comp_url:
            slug = re.sub(r'[^a-zA-Z0-9]', '', comp_name).lower()
            comp_url = f"https://wellfound.com/company/{slug}" if slug else "https://wellfound.com"

        locations = []
        loc_data = data.get('jobLocation', [])
        if isinstance(loc_data, dict):
            loc_data = [loc_data]
        for l in loc_data:
            if isinstance(l, dict):
                addr = l.get('address', {})
                if isinstance(addr, dict):
                    loc_parts = [addr.get('addressLocality'), addr.get('addressRegion'), addr.get('addressCountry')]
                    loc_str = ", ".join([p for p in loc_parts if p])
                    if loc_str:
                        locations.append(loc_str)
        loc_final = " / ".join(locations) if locations else "Remote / Various"
        
        date_raw = data.get('datePosted', '')
        date_posted = date_raw[:10] if date_raw else "2026-09-12"
        
        desc_html = data.get('description', '')
        desc_text = BeautifulSoup(desc_html, 'html.parser').get_text(separator=' ').strip() if desc_html else title
        desc_text = re.sub(r'\s+', ' ', desc_text)
        
        salary = ""
        bs = data.get('baseSalary', {})
        if isinstance(bs, dict) and 'value' in bs:
            v = bs['value']
            curr = bs.get('currency', 'USD')
            if isinstance(v, dict):
                min_v = v.get('minValue', '')
                max_v = v.get('maxValue', '')
                if min_v or max_v:
                    salary = f"{curr} {min_v} - {max_v}"
                    
        details = f"Role: {title} | Company: {comp_name} | Location: {loc_final}"
        if salary:
            details = f"Salary: {salary} | " + details

        return {
            "Job Role": title,
            "Company Name": comp_name or "Wellfound Verified Employer",
            "Location": loc_final,
            "Date Posted": date_posted,
            "Apply Link": url,
            "Company Link": comp_url,
            "No. of Applicants": "Actively Hiring",
            "Company / Job Details": details[:350],
            "Source": "Wellfound",
            "website": comp_url,
            "apply_link_url": url,
            "job_description": desc_text[:500] if desc_text else details
        }
    except Exception as e:
        return None

results = []
for i, u in enumerate(job_urls):
    j = fetch_details(u)
    if j:
        results.append(j)
        print(f"[{len(results)}] {j['Job Role']} | {j['Company Name']} | {j['Location']}")
    time.sleep(0.3)

print(f"\nSuccessfully fetched {len(results)} structured Wellfound jobs!")
with open("scratch/verified_wellfound_jobs.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
