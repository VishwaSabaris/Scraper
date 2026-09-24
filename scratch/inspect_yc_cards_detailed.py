from bs4 import BeautifulSoup
import re

with open("scratch/yc_page.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

# In scratch/yc_page.html, let's find all cards that contain job links
job_links = soup.find_all('a', href=lambda h: h and re.search(r'/jobs/\d+', h))
print(f"Total job links found: {len(job_links)}")

seen_cards = set()
for jl in job_links:
    # Walk up to find card container
    card = jl.parent
    for _ in range(8):
        if not card:
            break
        # Card container has border / rounded / bg classes
        classes = " ".join(card.get('class') or [])
        if 'border' in classes and ('rounded' in classes or 'p-3' in classes or 'p-4' in classes):
            break
        card = card.parent
        
    if not card or id(card) in seen_cards:
        continue
    seen_cards.add(id(card))
    
    # Within this card, examine all <a> tags
    all_a = card.find_all('a')
    print("\n--- NEW CARD ---")
    for a in all_a:
        href = a.get('href', '')
        text = " ".join(a.text.split())
        classes = a.get('class', [])
        print(f"  <a> class={classes} href={href} text={repr(text[:80])}")
        
    # Check if there is an external website link in this card
    ext_links = [a['href'] for a in all_a if a.get('href') and not a['href'].startswith('/') and 'workatastartup.com' not in a['href']]
    print(f"  External links: {ext_links}")
    
    if len(seen_cards) >= 5:
        break
