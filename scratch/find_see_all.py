from bs4 import BeautifulSoup

with open("scratch/yc_page.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

see_all = soup.find_all(string=lambda s: s and 'See all' in s)
print(f"Found {len(see_all)} 'See all' occurrences")
for sa in see_all[:10]:
    p = sa.parent
    print(f"Tag: <{p.name} href='{p.get('href')}' class='{p.get('class')}'> text: {repr(sa.strip())}")
    # Print the card containing this "See all"
    card = p
    for _ in range(6):
        if card and 'rounded' in (card.get('class') or []):
            break
        if card:
            card = card.parent
    if card:
        # What is the company link in this card?
        clinks = card.find_all('a', href=lambda h: h and '/companies/' in h)
        for cl in clinks:
            print(f"   clink: text={repr(cl.text.strip())} href={cl['href']}")
