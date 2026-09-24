import urllib.request
import urllib.parse
from bs4 import BeautifulSoup

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

for name, url in [
    ('Bing', 'https://www.bing.com/search?q=site%3Awellfound.com%2Fjobs+lead+generation'),
    ('Yahoo', 'https://search.yahoo.com/search?p=site%3Awellfound.com%2Fjobs+lead+generation')
]:
    try:
        req = urllib.request.Request(url, headers=headers)
        html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', href=True) if 'wellfound.com' in a['href']]
        print(name, 'wellfound links:', len(links))
        for l in links[:5]:
            print('  ', l)
    except Exception as e:
        print(name, 'error:', e)
