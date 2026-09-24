from bs4 import BeautifulSoup
import re

with open("scratch/yc_page.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

print("Title:", soup.title.text if soup.title else "No title")

# Check all links
links = soup.find_all('a')
comp_links = [a for a in links if a.get('href') and '/companies/' in a['href']]
job_links = [a for a in links if a.get('href') and '/jobs/' in a['href']]

print(f"Total links: {len(links)}")
print(f"Company links: {len(comp_links)}")
print(f"Job links: {len(job_links)}")

print("\n--- First 15 Company Links ---")
for cl in comp_links[:15]:
    print(f"href: {cl['href']} | text: {repr(cl.text.strip())} | class: {cl.get('class')}")

print("\n--- First 15 Job Links ---")
for jl in job_links[:15]:
    print(f"href: {jl['href']} | text: {repr(jl.text.strip())} | class: {jl.get('class')}")
