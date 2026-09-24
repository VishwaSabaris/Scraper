import urllib.parse
from filter_engine import UniversalJobFilter, FilterEngine

def run_tests():
    print("=" * 80)
    print("NAUKRI FILTER MATCHING & URL GENERATION TEST SUITE")
    print("=" * 80)

    # 1. Test Work Mode Mappings
    print("\n--- 1. Testing Work Mode (wfhType) ---")
    work_modes = [
        ("wfo", "0"),
        ("office", "0"),
        ("hybrid", "1"),
        ("remote", "2"),
        ("wfh", "2"),
        ("hybrid and remote", "1,2"),
        ("all", "0,1,2")
    ]
    for wm, expected in work_modes:
        uf = UniversalJobFilter(job_title="Data Analyst", location="Bangalore", work_mode=wm)
        params, _, _ = FilterEngine.adapt_for_portal("naukri", uf)
        assert params.get("wfhType") == expected, f"Failed for {wm}: expected {expected}, got {params.get('wfhType')}"
        print(f"  [PASS] work_mode='{wm}' -> wfhType='{params.get('wfhType')}'")

    # 2. Test Experience Values
    print("\n--- 2. Testing Experience (experience & naukriCampus) ---")
    exp_tests = [
        (0, "0", True),
        (1, "1", False),
        (2, "2", False),
        (3, "3", False),
        (5, "5", False)
    ]
    for exp_val, expected_exp, expected_campus in exp_tests:
        uf = UniversalJobFilter(job_title="Data Analyst", location="Bangalore", experience_min=exp_val)
        params, _, _ = FilterEngine.adapt_for_portal("naukri", uf)
        assert params.get("experience") == expected_exp, f"Failed exp {exp_val}: expected {expected_exp}, got {params.get('experience')}"
        if expected_campus:
            assert params.get("naukriCampus") == "true", f"Expected naukriCampus=true for exp {exp_val}"
            print(f"  [PASS] experience_min={exp_val} -> experience='{params.get('experience')}', naukriCampus='{params.get('naukriCampus')}'")
        else:
            print(f"  [PASS] experience_min={exp_val} -> experience='{params.get('experience')}'")

    # 3. Test Salary / CTC brackets
    print("\n--- 3. Testing Salary CTC Brackets (ctcFilter) ---")
    salary_tests = [
        (200000, "0to3"),
        (450000, "3to6"),
        (800000, "6to10"),
        (1200000, "10to15"),
        (2000000, "15to25"),
        (3500000, "25to50"),
        (6000000, "50to75"),
        (8500000, "75to100"),
        (15000000, "100to500")
    ]
    for s_val, expected_bracket in salary_tests:
        uf = UniversalJobFilter(job_title="Data Analyst", location="Bangalore", salary_min=s_val)
        params, _, _ = FilterEngine.adapt_for_portal("naukri", uf)
        assert params.get("ctcFilter") == expected_bracket, f"Failed salary {s_val}: expected {expected_bracket}, got {params.get('ctcFilter')}"
        print(f"  [PASS] salary_min={s_val} -> ctcFilter='{params.get('ctcFilter')}'")

    # 4. Test All 32 Departments
    print("\n--- 4. Testing All 32 Official Departments ---")
    all_32_departments = [
        "Engineering - Software & QA",
        "Sales & Business Development",
        "Customer Success, Service & Operations",
        "Data Science & Analytics",
        "IT & Information Security",
        "Engineering - Hardware & Networks",
        "Marketing & Communication",
        "Human Resources",
        "Finance & Accounting",
        "BFSI, Investments & Trading",
        "Research & Development",
        "Healthcare & Life Sciences",
        "Teaching & Training",
        "Production, Manufacturing & Engineering",
        "Other",
        "Administration & Facilities",
        "Product Management",
        "Content, Editorial & Journalism",
        "Procurement & Supply Chain",
        "Quality Assurance",
        "UX, Design & Architecture",
        "Food, Beverage & Hospitality",
        "Consulting",
        "Project & Program Management",
        "Media Production & Entertainment",
        "Strategic & Top Management",
        "Construction & Site Engineering",
        "CSR & Social Service",
        "Environment Health & Safety",
        "Legal & Regulatory",
        "Merchandising, Retail & eCommerce",
        "Security Services"
    ]

    for dept in all_32_departments:
        uf = UniversalJobFilter(job_title="Specialist", location="Bangalore", department=dept.lower())
        params, _, _ = FilterEngine.adapt_for_portal("naukri", uf)
        assert params.get("department") == dept, f"Failed department match for '{dept}': got '{params.get('department')}'"
        print(f"  [PASS] Dept match: '{dept}'")

    # 5. Test Exact Match with Reference URL
    print("\n--- 5. Testing Full URL Generation Matching Reference URL ---")
    # Reference URL:
    # https://www.naukri.com/data-analyst-jobs-in-bangalore?k=data%20analyst&l=bangalore&qproductJobSource=2&naukriCampus=true&nignbevent_src=jobsearchDeskGNB&experience=0&wfhType=2
    uf_ref = UniversalJobFilter(
        job_title="data analyst",
        location="bangalore",
        experience_min=0,
        work_mode="remote"
    )
    url = FilterEngine.build_portal_url("naukri", uf_ref)
    print(f"Generated URL:\n  {url}")
    assert "data-analyst-jobs-in-bangalore" in url
    assert "experience=0" in url
    assert "wfhType=2" in url
    assert "naukriCampus=true" in url
    assert "qproductJobSource=2" in url
    assert "nignbevent_src=jobsearchDeskGNB" in url
    print("  [PASS] URL contains all required query parameters and path elements!")

    print("\n" + "=" * 80)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
