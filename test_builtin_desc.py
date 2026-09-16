from curl_cffi import requests
from bs4 import BeautifulSoup

url = "https://builtin.com/job/associate-manager-sdr/11194695"
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
res = requests.get(url, headers=headers, impersonate="chrome120")
soup = BeautifulSoup(res.text, "html.parser")
for div in soup.find_all(['div', 'section']):
    txt = div.get_text().strip()
    if len(txt) > 500 and not div.find(['div', 'section']):
        print("Found text block:", div.get('class'), div.get('id'), len(txt))
        print(txt[:250])
        print("---")
# Also check for JSON-LD structured data
for script in soup.find_all('script', type='application/ld+json'):
    print("Found JSON-LD:", script.string[:300])
