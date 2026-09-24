with open('scratch/naukri_filtered_stream.txt', encoding='utf-8') as f:
    text = f.read()

import re, json

for key in ['jobDetails', 'jobs', 'tuples', 'title', 'companyName', 'placeholder']:
    matches = list(re.finditer(rf'"{key}":', text))
    print(f'Key "{key}": {len(matches)} matches')

# Search for any job data
for m in re.finditer(r'"(jobDetails|tuples|articles|results)":\s*(\[[^\]]+\])', text):
    print(m.group(1), "sample:", m.group(2)[:300])

for m in re.finditer(r'"title":\s*"([^"]+)"', text):
    print("title:", m.group(1))
