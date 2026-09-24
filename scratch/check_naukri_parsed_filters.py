from curl_cffi import requests
import re
import json

url = 'https://www.naukri.com/software-engineer-jobs-in-bangalore?k=software%20engineer&l=bangalore&experience=3&wfhType=2&ctcFilter=15to25&jobAge=7&sort=f'
print("Fetching:", url)
r = requests.get(url, impersonate='chrome120')
print("Status:", r.status_code)

raw_chunks = re.findall(r'self\.__next_f\.push\(\[\d+,\s*"(.*?)"\]\)', r.text, re.DOTALL)
full = ""
for c in raw_chunks:
    try:
        full += json.loads(f'"{c}"')
    except Exception:
        full += c

with open('scratch/naukri_filtered_stream.txt', 'w', encoding='utf-8') as f:
    f.write(full)

print(f"Full stream length: {len(full)}")

for key in ['searchParams', 'qsbParams', 'selectedFilters', 'urlMap', 'filterOrder']:
    for m in re.finditer(rf'"{key}":\s*(\{{[^}}]*\}}|\[[^\]]*\])', full):
        print(f"{key}: {m.group(1)}")
