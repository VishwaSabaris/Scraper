from bs4 import BeautifulSoup

with open("scratch/yc_page.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

jl = soup.find('a', href=lambda h: h and '/jobs/102423' in h)
card = jl.parent.parent
print("Card full text lines:")
for s in card.stripped_strings:
    print("  ->", repr(s))
