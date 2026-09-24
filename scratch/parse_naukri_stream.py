import re
import json

with open('scratch/naukri_page.html', encoding='utf-8') as f:
    html = f.read()

# Extract all self.__next_f pushes
# They look like: self.__next_f.push([1,"..."])
raw_matches = re.findall(r'self\.__next_f\.push\(\[\d+,\s*"(.*?)"\]\)', html, re.DOTALL)
print(f"Total raw __next_f chunks: {len(raw_matches)}")

full_text = ""
for m in raw_matches:
    try:
        # Decode JSON string escapes
        decoded = json.loads(f'"{m}"')
        full_text += decoded
    except Exception:
        full_text += m

with open('scratch/naukri_stream.txt', 'w', encoding='utf-8') as out:
    out.write(full_text)

print(f"Saved full stream ({len(full_text)} chars) to scratch/naukri_stream.txt")

# Search for filter names, clusters, facets
patterns = [
    r'(\w*[Ff]ilter\w*)',
    r'(\w*[Ff]acet\w*)',
    r'(\w*[Cc]luster\w*)',
    r'(\"wfhType[^\"]*\")',
    r'(\"experience[^\"]*\")',
    r'(\"salary[^\"]*\")',
    r'(\"cityTypeGid[^\"]*\")',
]

for pat in patterns:
    found = set(re.findall(pat, full_text))
    print(f"Pattern {pat}: {list(found)[:10]}")

# Look for filter dictionary or list
filter_block = re.findall(r'(\{"id":\s*"[^"]*",\s*"title":\s*"[^"]*"[^}]*\})', full_text)
print(f"Found {len(filter_block)} filter blocks:")
for b in filter_block[:10]:
    print("  ", b)
