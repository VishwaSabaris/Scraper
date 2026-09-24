from bs4 import BeautifulSoup
import re

with open("scratch/scrolled_se.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

jls = soup.find_all('a', href=lambda h: h and '/jobs/' in h)
print(f"Total job links: {len(jls)}")
for jl in jls:
    print(f"\nJL: {jl['href']} | class={jl.get('class')}")
    # Print its immediate text and children
    for c in jl.children:
        if c.name:
            print(f"  child <{c.name} class='{c.get('class')}'> text={repr(' '.join(c.text.split())[:80])}")
            
    # Check parent
    p = jl.parent
    for i in range(8):
        if not p: break
        c_links = [a for a in p.find_all('a') if a.get('href') and '/companies/' in a['href']]
        if c_links:
            print(f"  Parent {i+1} <{p.name}> has {len(c_links)} company links:")
            for cl in c_links[:3]:
                print(f"    cl: href={cl['href']} text={repr(cl.text.strip())}")
            break
        p = p.parent
