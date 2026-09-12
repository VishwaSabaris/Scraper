import os
import sys
import base64
import json
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from find_company_websites import get_dataforseo_auth_header

key = "bWFuaWthbUBibGF6bHkuYWk6MGM3OWU5NmE5Mzg2ODQ5ZQ=="
auth_header = get_dataforseo_auth_header(key)
headers = {
    "Authorization": auth_header,
    "Content-Type": "application/json"
}

serp_url = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"
payload = [{
    "keyword": "Monzo Bank official website",
    "language_code": "en",
    "depth": 10,
    "tag": "Monzo"
}]

res = requests.post(serp_url, headers=headers, json=payload, timeout=30)
data = res.json()
print(json.dumps(data, indent=2))
