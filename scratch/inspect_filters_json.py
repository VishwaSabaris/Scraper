with open('scratch/naukri_stream.txt', encoding='utf-8') as f:
    text = f.read()

import re, json

# Find occurrences of filterOrder
for m in re.finditer(r'filterOrder', text):
    start = max(0, m.start() - 100)
    end = min(len(text), m.end() + 2000)
    print("MATCH AROUND filterOrder:")
    print(text[start:end])
    print("=" * 60)

# Find any JSON blocks with filter
for m in re.finditer(r'"filters":', text):
    start = max(0, m.start() - 50)
    end = min(len(text), m.end() + 3000)
    print("MATCH AROUND \"filters\":")
    print(text[start:end])
    print("=" * 60)
