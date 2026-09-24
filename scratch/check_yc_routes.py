import requests

for path in ['/jobs', '/companies', '/jobs?query=python']:
    url = f"https://www.workatastartup.com{path}"
    r = requests.get(url, allow_redirects=False, headers={'User-Agent': 'Mozilla/5.0'})
    print(f"{url} -> status {r.status_code}, location: {r.headers.get('Location')}")
