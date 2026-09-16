import re
import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Example LinkedIn job URL
url = "https://in.linkedin.com/jobs/view/sales-development-representative-india-at-infosectrain-4158498877"
job_id_match = re.search(r'(\d{8,12})', url)
if job_id_match:
    job_id = job_id_match.group(1)
    api_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
    res = requests.get(api_url, headers=headers, timeout=10)
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        soup = BeautifulSoup(res.text, 'html.parser')
        desc_el = soup.select_one('.show-more-less-html__markup, .description__text, section.description')
        if desc_el:
            clean_text = ' '.join(desc_el.get_text().split())
            print(f"Success! Description length: {len(clean_text)} chars")
            print(f"Snippet: {clean_text[:200]}...")
