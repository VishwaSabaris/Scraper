from bs4 import BeautifulSoup
import re

with open("./scratch/apna_sample.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

# Check all links with /job/
links = soup.find_all("a", href=re.compile(r"^/job/"))
print(f"Total job links in Apna: {len(links)}")

for idx, a in enumerate(links[:5]):
    # Get card parent
    card = a
    for _ in range(4):
        if card.parent:
            card = card.parent
    
    # Print card texts
    texts = [t.strip() for t in card.stripped_strings if t.strip()]
    print(f"\n--- Apna Card {idx} ---")
    print("Href:", a.get("href"))
    print("Card strings:", texts[:10])
