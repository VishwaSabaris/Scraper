"""
Unit & Integration Test Script for Proxy System
"""
import os
import sys
import time

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from proxy_manager import ProxyManager
from request_client import execute_request

def test_proxy_manager_parsing():
    print("[*] Testing Proxy Parsing Formats...")
    p1 = ProxyManager.parse_proxy_string("1.2.3.4:8080")
    assert p1["url"] == "http://1.2.3.4:8080", f"Failed p1: {p1}"

    p2 = ProxyManager.parse_proxy_string("http://5.6.7.8:3128")
    assert p2["url"] == "http://5.6.7.8:3128", f"Failed p2: {p2}"

    p3 = ProxyManager.parse_proxy_string("user:pass@9.10.11.12:80")
    assert p3["url"] == "http://user:pass@9.10.11.12:80", f"Failed p3: {p3}"
    assert p3["username"] == "user" and p3["password"] == "pass"

    p_invalid = ProxyManager.parse_proxy_string("not_a_proxy")
    assert p_invalid is None
    print("[+] Proxy parsing tests passed successfully.")

def test_rotation_and_health():
    print("[*] Testing Round-Robin Rotation and Cooldown Health Mechanism...")
    pm = ProxyManager(enabled=True)
    pm.failure_threshold = 2
    pm.cooldown_seconds = 2

    # Inject mock proxies
    pm._proxies = [
        ProxyManager.parse_proxy_string("10.0.0.1:8080"),
        ProxyManager.parse_proxy_string("10.0.0.2:8080"),
    ]

    # Test round robin
    prox1 = pm.get_proxy("raw")
    prox2 = pm.get_proxy("raw")
    prox3 = pm.get_proxy("raw")

    assert prox1 == "http://10.0.0.1:8080"
    assert prox2 == "http://10.0.0.2:8080"
    assert prox3 == "http://10.0.0.1:8080"
    print("[+] Round-robin rotation order verified.")

    # Test failure threshold and cooldown
    pm.mark_failure(prox1)
    assert pm._proxies[0]["failure_count"] == 1
    assert pm._proxies[0]["disabled_until"] is None

    pm.mark_failure(prox1) # Second failure reaches threshold
    assert pm._proxies[0]["failure_count"] == 2
    assert pm._proxies[0]["disabled_until"] is not None

    # Next call should skip 10.0.0.1 (in cooldown) and return 10.0.0.2
    active = pm.get_proxy("raw")
    assert active == "http://10.0.0.2:8080"
    print("[+] Failure threshold and cooldown temporary disable verified.")

    # Sleep past cooldown and verify re-enabling
    time.sleep(2.1)
    reenabled = pm.get_proxy("raw")
    assert pm._proxies[0]["disabled_until"] is None
    print("[+] Cooldown expiration and proxy auto-recovery verified.")

def test_proxy_disabled_mode():
    print("[*] Testing Disabled Proxy Mode...")
    pm = ProxyManager(enabled=False)

    proxy = pm.get_proxy("requests")
    assert proxy is None, "Disabled manager should return None"
    print("[+] Disabled mode fallback verified.")

if __name__ == "__main__":
    test_proxy_manager_parsing()
    test_rotation_and_health()
    test_proxy_disabled_mode()
    print("\n[++++] ALL PROXY SYSTEM UNIT TESTS PASSED CLEANLY!")
