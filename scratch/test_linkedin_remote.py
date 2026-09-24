import sys
import os
sys.path.insert(0, os.path.abspath("."))
from filter_engine import UniversalJobFilter, FilterEngine

uf1 = UniversalJobFilter(keywords='Python Developer', location='New York', work_mode='remote')
p, a, o = FilterEngine.adapt_for_portal('linkedin', uf1)
print("Case 1 (location=New York, work_mode=remote):")
print("  Params:", p)
print("  Applied:", a)
print("  Omitted:", o)

uf2 = UniversalJobFilter(keywords='Python Developer', location='remote', work_mode='')
p2, a2, o2 = FilterEngine.adapt_for_portal('linkedin', uf2)
print("\nCase 2 (location=remote, work_mode=''):")
print("  Params:", p2)
print("  Applied:", a2)
print("  Omitted:", o2)
