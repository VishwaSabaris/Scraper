import os
import sys
import time
import requests
import json

def get_direct_ip():
    try:
        r = requests.get("https://api.ipify.org?format=json", timeout=5)
        return r.json().get("ip")
    except Exception:
        try:
            r = requests.get("http://api.ipify.org?format=json", timeout=5)
            return r.json().get("ip")
        except Exception as e:
            return f"Unavailable ({e})"

def test_proxy(proxy_url, direct_ip, timeout=5):
    p = proxy_url.strip()
    if not (p.startswith("http://") or p.startswith("https://") or p.startswith("socks5://")):
        p = f"http://{p}"

    proxies = {"http": p, "https": p}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    report = {
        "proxy": p,
        "http_ok": False,
        "http_latency": None,
        "http_ip": None,
        "https_ok": False,
        "https_latency": None,
        "https_ip": None,
        "anonymous": False,
        "error": None
    }

    # 1. HTTP Check
    try:
        t0 = time.perf_counter()
        r = requests.get("http://api.ipify.org?format=json", proxies=proxies, headers=headers, timeout=timeout)
        report["http_latency"] = round(time.perf_counter() - t0, 2)
        if r.status_code == 200:
            report["http_ok"] = True
            report["http_ip"] = r.json().get("ip")
    except Exception as e:
        report["http_error"] = type(e).__name__

    # 2. HTTPS Check (CONNECT Tunneling)
    try:
        t0 = time.perf_counter()
        r = requests.get("https://api.ipify.org?format=json", proxies=proxies, headers=headers, timeout=timeout)
        report["https_latency"] = round(time.perf_counter() - t0, 2)
        if r.status_code == 200:
            report["https_ok"] = True
            report["https_ip"] = r.json().get("ip")
    except Exception as e:
        report["https_error"] = type(e).__name__

    observed_ip = report["https_ip"] or report["http_ip"]
    if observed_ip and observed_ip != direct_ip and "Unavailable" not in direct_ip:
        report["anonymous"] = True

    return report

def main():
    file_path = "data/low_latency_proxies.txt"
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        proxies = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    direct_ip = get_direct_ip()
    print("=" * 65)
    print("           DETAILED PROXY POOL HEALTH CHECK          ")
    print("=" * 65)
    print(f"[*] Caller Direct IP (without proxy): {direct_ip}")
    print(f"[*] Testing {len(proxies)} proxies from '{file_path}'...\n")

    results = []
    for i, p in enumerate(proxies, 1):
        print(f"[{i}/{len(proxies)}] Testing {p} ...", end=" ", flush=True)
        res = test_proxy(p, direct_ip, timeout=5)
        results.append(res)
        
        status_parts = []
        if res["http_ok"]:
            status_parts.append(f"HTTP: OK ({res['http_latency']}s)")
        else:
            status_parts.append(f"HTTP: FAIL ({res.get('http_error', 'ERR')})")
            
        if res["https_ok"]:
            status_parts.append(f"HTTPS: OK ({res['https_latency']}s)")
        else:
            status_parts.append(f"HTTPS: FAIL ({res.get('https_error', 'ERR')})")
            
        print(" | ".join(status_parts))

    print("\n" + "=" * 65)
    print("                      SUMMARY REPORT                         ")
    print("=" * 65)

    fully_working = [r for r in results if r["http_ok"] and r["https_ok"]]
    https_only = [r for r in results if r["https_ok"] and not r["http_ok"]]
    http_only = [r for r in results if r["http_ok"] and not r["https_ok"]]
    dead = [r for r in results if not r["http_ok"] and not r["https_ok"]]

    print(f"Total Proxies Tested : {len(results)}")
    print(f"Fully Working (HTTP + HTTPS) : {len(fully_working)}")
    print(f"HTTPS Only (CONNECT Works)   : {len(https_only)}")
    print(f"HTTP Only                    : {len(http_only)}")
    print(f"Dead / Unresponsive          : {len(dead)}")
    print("-" * 65)

    if fully_working:
        print("\n[+] RECOMMENDED FOR SCRAPING (Dual HTTP & HTTPS):")
        for r in fully_working:
            print(f"  * {r['proxy']} (Latency: HTTP {r['http_latency']}s / HTTPS {r['https_latency']}s, Exit IP: {r['https_ip']}, Masked: {r['anonymous']})")

    if https_only:
        print("\n[~] HTTPS-ONLY PROXIES (Works for HTTPS scraping like LinkedIn/Portals):")
        for r in https_only:
            print(f"  * {r['proxy']} (Latency: HTTPS {r['https_latency']}s, Exit IP: {r['https_ip']}, Masked: {r['anonymous']})")

    if http_only:
        print("\n[!] HTTP-ONLY PROXIES (Cannot tunnel HTTPS):")
        for r in http_only:
            print(f"  * {r['proxy']} (Latency: HTTP {r['http_latency']}s, Exit IP: {r['http_ip']})")

    if dead:
        print("\n[-] DEAD PROXIES (Should be removed):")
        for r in dead:
            print(f"  * {r['proxy']}")

if __name__ == "__main__":
    main()
