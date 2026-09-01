"""
Test Proxy Rotation & Refresher Script
=======================================
Validates multiple proxy rotation behavior and proxy refresh pipeline
against a neutral IP reflection endpoint.
"""

import os
import sys
import logging
import requests

from proxy_manager import get_default_proxy_manager
from proxy_refresher import ProxyRefresher
from request_client import execute_request

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("TestProxyRotation")


def run_test_a():
    """Test A — Multiple proxy rotation"""
    print("\n" + "=" * 50)
    print("      TEST A: MULTIPLE PROXY ROTATION TEST      ")
    print("=" * 50)

    pm = get_default_proxy_manager()
    stats = pm.get_stats()
    print(f"[*] ProxyManager Status: Enabled={pm.enabled}, Total={stats['total']}, Active={stats['active']}")

    if stats["active"] == 0:
        print("[!] Warning: No active proxies available in data/valid_proxies.txt.")
        print("[*] Please run the validation script or run Test B first.")
        return

    test_url = "http://api.ipify.org?format=json"
    print(f"[*] Sending 5 sequential requests to: {test_url}\n")

    for i in range(1, 6):
        print(f"--- Attempt {i}/5 ---")
        try:
            # We fetch proxy config specifically to inspect what proxy gets selected
            proxy_config = pm.get_proxy(target="requests")
            print(f"Selected Proxy: {proxy_config}")

            # Send the request
            response = execute_request(
                url=test_url,
                method="GET",
                proxy_manager=pm,
                timeout=10,
                max_retries=1
            )
            
            observed_ip = response.json().get("ip")
            print(f"Observed IP: {observed_ip}")
            print("Status: SUCCESS")
        except Exception as err:
            print(f"Status: FAILURE | Error: {err}")
        print("-" * 30)


def run_test_b():
    """Test B — Refresh integration"""
    print("\n" + "=" * 50)
    print("      TEST B: REFRESH INTEGRATION TEST          ")
    print("=" * 50)

    pm = get_default_proxy_manager()
    initial_stats = pm.get_stats()
    print(f"[*] Initial Proxy Count (data/valid_proxies.txt): {initial_stats['total']}")

    refresher = ProxyRefresher(pm)
    print("[*] Triggering immediate controlled refresh cycle...")
    refresher.refresh_once()

    # Re-fetch stats
    refreshed_stats = pm.get_stats()
    
    # Read stats from files
    raw_count = 0
    if os.path.exists(refresher.raw_file):
        with open(refresher.raw_file, "r", encoding="utf-8") as f:
            raw_count = sum(1 for line in f if line.strip() and not line.startswith("#"))

    print("\n--- Refresh Summary ---")
    print(f"[*] Raw Proxies in Snapshot File: {raw_count}")
    print(f"[*] Validated Working Proxies   : {refreshed_stats['total']}")
    print(f"[*] Active Pool Count           : {refreshed_stats['active']}")
    print("-----------------------")

    # Run a few neutral requests using the refreshed pool
    test_url = "http://api.ipify.org?format=json"
    print(f"\n[*] Running 3 test requests with newly refreshed pool:")
    for i in range(1, 4):
        print(f"Request {i}/3")
        try:
            response = execute_request(
                url=test_url,
                method="GET",
                proxy_manager=pm,
                timeout=10,
                max_retries=1
            )
            print(f"  Observed IP: {response.json().get('ip')} | Status: SUCCESS")
        except Exception as err:
            print(f"  Status: FAILURE | Error: {err}")


if __name__ == "__main__":
    # Ensure raw files and folders exist
    os.makedirs("data", exist_ok=True)
    
    # Run the tests
    run_test_b()
    run_test_a()
