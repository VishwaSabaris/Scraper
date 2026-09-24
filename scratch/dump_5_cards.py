from bs4 import BeautifulSoup
import re

with open("scratch/yc_page.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

job_links = soup.find_all('a', href=lambda h: h and re.search(r'/jobs/\d+', h))
seen = set()
for jl in job_links:
    card = jl.find_parent(class_=lambda c: c and ('border-gray-200' in c or 'rounded' in c))
    if not card or id(card) in seen:
        continue
    seen.add(id(card))
    strings = list(card.stripped_strings)
    print("CARD:", strings)
    if len(seen) >= 5:
        break
