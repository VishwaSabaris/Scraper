from ddgs import DDGS

tests = [
    ("Columbus, OH", "Sales Development Representative"),
    ("Orlando, FL", "Sales Development Representative"),
    ("Clearwater, FL", "Sales Development Representative"),
    ("San Francisco, CA", "Sales Development Representative SDR"),
    ("Indianapolis, IN", "Business Development Representative"),
    ("Philadelphia, PA", "Sales Development Representative"),
    ("San Antonio, TX", "Business Development Representative Inside Sales"),
    ("New York, NY", "Sr. Sales Development Representative"),
    ("St. Louis, MO", "Sales Development Representative 2"),
    ("Redwood City, CA", "Senior Enterprise Sales Development Representative"),
    ("Santa Monica, CA", "Sales Development Representative"),
    ("Oak Park, IL", "Sales Development Representative Insurance"),
    ("Tampa, FL", "Sales Development Representative")
]

with DDGS() as ddgs:
    for loc, role in tests:
        q = f'careerbuilder "{role}" "{loc}"'
        print(f"\nQuery: {q}")
        try:
            hits = list(ddgs.text(q, max_results=3))
            for h in hits:
                print("  Title:", h.get('title'))
                print("  Body :", h.get('body'))
        except Exception as e:
            print("  Error:", e)
