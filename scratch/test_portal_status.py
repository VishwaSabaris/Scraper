import sys
import os
sys.path.insert(0, os.path.abspath("."))
from scrape_all_jobs_master import PORTAL_REGISTRY

print(f"Total portals in registry: {len(PORTAL_REGISTRY)}")
for key, val in PORTAL_REGISTRY.items():
    print(f"{key:16} : {val['name']:25} | async: {val['is_async']} | func: {val['func'].__name__}")
