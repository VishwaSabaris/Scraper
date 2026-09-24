import sys, os
sys.path.insert(0, os.path.abspath("."))

from scrape_all_jobs_master import (
    PORTAL_REGISTRY,
    ORDERED_PORTAL_KEYS,
    INDEX_TO_PORTAL,
    display_selective_portals_menu,
    resolve_selective_portals,
    INDIAN_PORTALS,
    GLOBAL_PORTALS
)

def run_tests():
    print("=" * 60)
    print("TEST 1: Visual layout of display_selective_portals_menu()")
    print("=" * 60)
    display_selective_portals_menu()

    print("=" * 60)
    print("TEST 2: Verify Index 1 is Adzuna and Index 2 is Apna")
    print("=" * 60)
    assert INDEX_TO_PORTAL[1] == "adzuna", f"Expected 'adzuna' at 1, got {INDEX_TO_PORTAL[1]}"
    assert PORTAL_REGISTRY["adzuna"]["name"] == "Adzuna"
    print(f"Index 1: {INDEX_TO_PORTAL[1]} -> {PORTAL_REGISTRY['adzuna']['name']} [PASSED]")
    assert INDEX_TO_PORTAL[2] == "apna", f"Expected 'apna' at 2, got {INDEX_TO_PORTAL[2]}"
    print(f"Index 2: {INDEX_TO_PORTAL[2]} -> {PORTAL_REGISTRY['apna']['name']} [PASSED]")

    print("\n" + "=" * 60)
    print("TEST 3: Resolve '1,2,5,6'")
    print("=" * 60)
    res_1256 = resolve_selective_portals("1,2,5,6")
    expected_1256 = ["adzuna", "apna", "careerjet", "dice"]
    assert res_1256 == expected_1256, f"Expected {expected_1256}, got {res_1256}"
    print(f"Input '1,2,5,6' -> {res_1256} [PASSED]")

    print("\n" + "=" * 60)
    print("TEST 4: Resolve with spaces ' 1 , 2 , 5 , 6 '")
    print("=" * 60)
    res_spaces = resolve_selective_portals(" 1 , 2 , 5 , 6 ")
    assert res_spaces == expected_1256, f"Expected {expected_1256}, got {res_spaces}"
    print(f"Input ' 1 , 2 , 5 , 6 ' -> {res_spaces} [PASSED]")

    print("\n" + "=" * 60)
    print("TEST 5: Resolve with portal names/format '1-adzuna, 2-apna'")
    print("=" * 60)
    res_fmt = resolve_selective_portals("1-adzuna, 2-apna")
    assert res_fmt == ["adzuna", "apna"], f"Expected ['adzuna', 'apna'], got {res_fmt}"
    print(f"Input '1-adzuna, 2-apna' -> {res_fmt} [PASSED]")

    print("\n" + "=" * 60)
    print("TEST 6: Resolve range '1-4, 6'")
    print("=" * 60)
    res_range = resolve_selective_portals("1-4, 6")
    expected_range = ["adzuna", "apna", "builtin", "careerbuilder", "dice"]
    assert res_range == expected_range, f"Expected {expected_range}, got {res_range}"
    print(f"Input '1-4, 6' -> {res_range} [PASSED]")

    print("\n" + "=" * 60)
    print("TEST 7: Check Total Registered Portals")
    print("=" * 60)
    print(f"Total Ordered Portals: {len(ORDERED_PORTAL_KEYS)}")
    print(f"Total Indian Portals: {len(INDIAN_PORTALS)}")
    print(f"Total Global Portals: {len(GLOBAL_PORTALS)}")
    assert len(ORDERED_PORTAL_KEYS) >= 26, "Expected at least 26 portals"
    print("Portal count verified [PASSED]")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
