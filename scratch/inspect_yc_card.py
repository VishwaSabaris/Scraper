from bs4 import BeautifulSoup

with open("scratch/yc_page.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

# Find the container for Tank Payments or another company
tank = soup.find('a', href=lambda h: h and '/companies/tank-payments' in h)
if tank:
    # Print its ancestor hierarchy
    p = tank
    for i in range(6):
        p = p.parent
        print(f"Ancestor {i+1}: <{p.name} class='{p.get('class')}'>")
        # Check if this ancestor contains jobs
        jobs = p.find_all('a', href=lambda h: h and '/jobs/' in h)
        if jobs:
            print(f"  --> Found {len(jobs)} jobs inside ancestor {i+1}!")
            for j in jobs:
                print(f"      Job: {j.text.strip()} -> {j['href']}")
            # Also check if this ancestor contains "See all X jobs" link
            more_links = p.find_all('a', href=lambda h: h and '/companies/' in h)
            for m in more_links:
                print(f"      Company-link inside card: {repr(m.text.strip())} -> {m['href']} | class: {m.get('class')}")
            break
