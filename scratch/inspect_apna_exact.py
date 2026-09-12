from bs4 import BeautifulSoup

with open("./scratch/apna_sample.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

links = soup.find_all("a", href=lambda h: h and h.startswith("/job/"))
print("Total job links:", len(links))

for idx, a in enumerate(links[:3]):
    print(f"\n--- Job Card Link {idx} ---: {a.get('href')}")
    # Inspect children inside <a>
    for child in a.find_all(["h2", "h3", "h4", "p", "span", "div"]):
        txt = child.text.strip()
        cl = child.get("class", [])
        if txt and len(cl) > 0:
            print(f"  Tag: {child.name} | Class: {cl} | Text: {txt[:60]}")
