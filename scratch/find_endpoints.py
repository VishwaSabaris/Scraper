import re

with open('scratch/naukri_page.html', encoding='utf-8') as f:
    html = f.read()

# Look for api endpoints or fetch paths
urls = set(re.findall(r'https?://[a-zA-Z0-9.-]+\.naukri\.com/[a-zA-Z0-9_./?-]*', html))
print("Found naukri URLs:")
for u in sorted(urls):
    if any(k in u for k in ['api', 'search', 'job', 'v3', 'v2', 'v1', 'filter', 'suggest']):
        print("  ", u)

# Also look for relative endpoints like /jobapi/... or /jobsearch/...
rel_endpoints = set(re.findall(r'["\'](/job[a-zA-Z0-9_/.-]*)["\']', html))
print("Relative job endpoints:")
for ep in sorted(rel_endpoints):
    print("  ", ep)
