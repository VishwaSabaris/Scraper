import requests
from proxy_manager import ProxyManager

def main():
    # Initialize proxy manager
    proxy_manager = ProxyManager(proxy_file="data/valid_proxies.txt")
    
    # We will query httpbin.org/ip to see the exact IP and headers
    test_url = "http://httpbin.org/ip"
    
    print("\n=== Active Proxy Routing & Anonymity Check ===")
    
    tested = 0
    success = 0
    
    # Let's test the first 5 rotated proxies
    for attempt in range(1, 6):
        proxy_config = proxy_manager.get_proxy(target="requests")
        if not proxy_config:
            print("[!] No active proxies available.")
            break
            
        proxy_url = proxy_config["http"]
        print(f"\n[{attempt}/5] Testing Proxy: {proxy_url}")
        
        try:
            # We also query headers to check for X-Forwarded-For leaks
            response = requests.get(
                "http://httpbin.org/get", 
                proxies=proxy_config, 
                timeout=8
            )
            response.raise_for_status()
            data = response.json()
            
            origin_ip = data.get("origin", "")
            headers = data.get("headers", {})
            
            # Check if our real IP (106.192.173.44) is leaked in the origin or headers
            real_ip = "106.192.173.44"
            is_leaked = real_ip in origin_ip or any(real_ip in str(val) for val in headers.values())
            
            print(f"  -> Destination Server sees IP: {origin_ip}")
            if is_leaked:
                print("  -> Anonymity: TRANSPARENT (Your real IP was detected!)")
            else:
                print("  -> Anonymity: HIGH (Elite/Anonymous - Real IP hidden)")
                
            proxy_manager.mark_success(proxy_config)
            success += 1
            
        except Exception as e:
            print(f"  -> Connection failed: {e}")
            proxy_manager.mark_failure(proxy_config)
            
        tested += 1

    print(f"\n=== Test Completed: {success}/{tested} succeeded ===")

if __name__ == "__main__":
    main()