import urllib.request

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

candidates = [
    'sales', 'sales-development-representative', 'business-development', 'sales-manager',
    'account-executive', 'account-manager', 'marketing', 'growth-marketer', 'lead-generation',
    'software-engineer', 'frontend-engineer', 'backend-engineer', 'full-stack-engineer',
    'data-analyst', 'data-engineer', 'data-scientist', 'devops', 'devops-engineer',
    'product-manager', 'designer', 'ui-ux-designer', 'product-designer',
    'operations-manager', 'operations', 'recruiter', 'human-resources',
    'finance', 'financial-analyst', 'customer-success-manager', 'customer-support'
]

valid = []
for r in candidates:
    url = f'https://wellfound.com/role/l/{r}/india'
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                valid.append(r)
    except Exception as e:
        pass

print("Valid role slugs in /role/l/{role}/india:")
print(valid)
