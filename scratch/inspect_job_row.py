from bs4 import BeautifulSoup
import re

with open("scratch/yc_page.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

jl = soup.find('a', href=lambda h: h and '/jobs/102423' in h)
if jl:
    # Walk parents up to 4 levels
    p = jl
    for i in range(4):
        p = p.parent
        print(f"Parent {i+1} (<{p.name} class='{p.get('class')}'>):")
        print(p.prettify()[:600])
        print("=" * 40)
