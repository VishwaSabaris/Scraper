import sys
import time
import requests
import argparse

def get_direct_ip():
    """Detects caller's actual direct IP."""
    try:
        res = requests.get("https://api.ipify.org?format=json", timeout=5)
        return res.json().get("ip")
    except Exception:
        try:
            res = requests.get("http://api.ipify.org?format=json", timeout=5)
            return res.json().get("ip")
        except Exception as e:
            return f"Error: {e}"

def test_proxy(proxy_str, test_target=None, timeout=6):
    """
    Tests both HTTP and HTTPS connectivity for a given proxy.
    Checks latency, observed IP, and whether it masks the real IP.
    """
    p = proxy_str.strip()
    if not (p.startswith("http://") or p.startswith("https://") or p.startswith("socks5://")):
        p = f"http://{p}"

    proxies = {"http": p, "https": p}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    results = {}

    # 1. Test HTTP
    t0 = time.perf_counter()
    try:
        r_http = requests.get("http://api.ipify.org?format=json", proxies=proxies, headers=headers, timeout=timeout)
        elapsed_http = time.perf_counter() - t0
        if r_http.status_code == 200:
            results["http"] = {"ok": True, "ip": r_http.json().get("ip"), "latency": elapsed_http}
        else:
            results["http"] = {"ok": False, "error": f"HTTP {r_http.status_code}", "latency": elapsed_http}
    except Exception as e:
        results["http"] = {"ok": False, "error": type(e).__name__, "latency": time.perf_counter() - t0}

    # 2. Test HTTPS (Tunneling / CONNECT)
    t0 = time.perf_counter()
    try:
        r_https = requests.get("https://api.ipify.org?format=json", proxies=proxies, headers=headers, timeout=timeout)
        elapsed_https = time.perf_counter() - t0
        if r_https.status_code == 200:
            results["https"] = {"ok": True, "ip": r_https.json().get("ip"), "latency": elapsed_https}
        else:
            results["https"] = {"ok": False, "error": f"HTTP {r_https.status_code}", "latency": elapsed_https}
    except Exception as e:
        results["https"] = {"ok": False, "error": type(e).__name__, "latency": time.perf_counter() - t0}

    # 3. Optional specific target URL test
    if test_target:
        t0 = time.perf_counter()
        try:
            r_target = requests.get(test_target, proxies=proxies, headers=headers, timeout=timeout)
            elapsed_target = time.perf_counter() - t0
            results["target"] = {"ok": r_target.status_code in (200, 301, 302), "status": r_target.status_code, "latency": elapsed_target}
        except Exception as e:
            results["target"] = {"ok": False, "error": type(e).__name__, "latency": time.perf_counter() - t0}

    return results

def main():
    parser = argparse.ArgumentParser(description="Test proxy validity, latency, and anonymity")
    parser.add_argument("proxy", nargs="?", default=None, help="Proxy string (e.g. 1.2.3.4:8080 or http://user:pass@ip:port)")
    parser.add_argument("--file", "-f", default=None, help="File containing proxy list to test")
    parser.add_argument("--target", "-t", default=None, help="Custom target URL to test through proxy (e.g. https://www.linkedin.com)")
    parser.add_argument("--timeout", type=int, default=5, help="Request timeout in seconds (default: 5)")
    args = parser.parse_args()

    print("=" * 60)
    print("                PROXY VALIDATION TOOL               ")
    print("=" * 60)

    direct_ip = get_direct_ip()
    print(f"[*] Your Direct IP (without proxy): {direct_ip}\n")

    if args.proxy:
        proxies_to_test = [args.proxy]
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            proxies_to_test = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    else:
        # Default to low_latency_proxies.txt if exists
        default_file = "data/low_latency_proxies.txt"
        try:
            with open(default_file, "r", encoding="utf-8") as f:
                proxies_to_test = [l.strip() for l in f if l.strip() and not l.startswith("#")]
            print(f"[*] No proxy provided. Testing {len(proxies_to_test)} proxies from {default_file}:\n")
        except Exception:
            proxies_to_test = []

    if not proxies_to_test:
        print("[!] No proxies found to test. Provide one as an argument: python scratch/test_proxy_check.py <ip:port>")
        return

    working_count = 0
    for idx, p in enumerate(proxies_to_test, 1):
        print(f"[{idx}/{len(proxies_to_test)}] Testing: {p}")
        res = test_proxy(p, test_target=args.target, timeout=args.timeout)

        http_info = res.get("http", {})
        https_info = res.get("https", {})

        is_any_ok = http_info.get("ok") or https_info.get("ok")
        if is_any_ok:
            working_count += 1
            observed_ip = http_info.get("ip") or https_info.get("ip")
            anonymous = "ANONYMOUS (IP masked)" if observed_ip != direct_ip else "WARNING: Real IP Leaked"
            print(f"  --> Status:   WORKING ({anonymous})")
            print(f"  --> Exit IP:  {observed_ip}")
            if http_info.get("ok"):
                print(f"  --> HTTP:     PASS (Latency: {http_info['latency']:.2f}s)")
            else:
                print(f"  --> HTTP:     FAIL ({http_info.get('error')})")
            if https_info.get("ok"):
                print(f"  --> HTTPS:    PASS (Latency: {https_info['latency']:.2f}s)")
            else:
                print(f"  --> HTTPS:    FAIL ({https_info.get('error')})")
        else:
            print(f"  --> Status:   DEAD / FAILED")
            print(f"  --> HTTP:     {http_info.get('error')}")
            print(f"  --> HTTPS:    {https_info.get('error')}")

        if "target" in res:
            t = res["target"]
            status = "PASS" if t.get("ok") else "FAIL"
            print(f"  --> Target:   {args.target} [{status}] ({t.get('status') or t.get('error')})")

        print("-" * 60)

    print(f"\n[+] Summary: {working_count}/{len(proxies_to_test)} working proxies.")

if __name__ == "__main__":
    main()
