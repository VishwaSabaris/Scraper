from curl_cffi import requests
import urllib.parse, json, re

params = {
    'k': 'c',
    'l': 'Chennai',
    'wfhType': '3',
    'experience': '3-5',
    'ctcFilter': '6to10',
    'jobAge': '7',
    'jobType': '1',
    'skills': 'Node.js, MongoDB',
    'industry': 'IT Services & Consulting',
    'education': 'B.Tech/B.E.',
    'cityTypeGid': '9513',
    'sort': 'r'
}

url = f'https://www.naukri.com/c-jobs-in-chennai?{urllib.parse.urlencode(params)}'
print('Testing TC-02 Naukri URL:', url)
r = requests.get(url, impersonate='chrome120')
print('Status:', r.status_code)

raw_chunks = re.findall(r'self\.__next_f\.push\(\[\d+,\s*"(.*?)"\]\)', r.text, re.DOTALL)
full = ''
for c in raw_chunks:
    try:
        full += json.loads(f'"{c}"')
    except Exception:
        full += c

for m in re.finditer(r'"searchParams":\s*(\{[^}]+\})', full):
    print('Parsed searchParams:', m.group(1))
