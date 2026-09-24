import sys, os
sys.path.insert(0, os.path.abspath("."))
from scrape_all_jobs_master import PORTAL_REGISTRY, INDIAN_PORTALS, GLOBAL_PORTALS

sorted_keys = sorted(PORTAL_REGISTRY.keys())
print(f"Total Portals in PORTAL_REGISTRY: {len(sorted_keys)}")
for idx, key in enumerate(sorted_keys, 1):
    info = PORTAL_REGISTRY[key]
    print(f"{idx:2d} - {info['name']} ({key}) | Region: {info.get('region', 'N/A')}")
