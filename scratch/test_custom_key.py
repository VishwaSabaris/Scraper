import os
import sys
import base64
import json
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from find_company_websites import get_dataforseo_auth_header

def test_custom_key(api_key: str):
    print(f"[*] Testing API Key: {api_key[:6]}...{api_key[-6:]}")
    
    # Let's see what the decoded login is
    try:
        decoded = base64.b64decode(api_key).decode("utf-8")
        login_part = decoded.split(":")[0] if ":" in decoded else "N/A"
        print(f"[*] Decoded Login: {login_part}")
    except Exception as e:
        print(f"[*] Base64 decode note: {e}")

    auth_header = get_dataforseo_auth_header(api_key)
    headers = {
        "Authorization": auth_header,
        "Content-Type": "application/json"
    }

    # Test 1: User Data / Balance
    print("\n--- Test 1: Checking Account User Data / Balance ---")
    user_data_url = "https://api.dataforseo.com/v3/appendix/user_data"
    try:
        res = requests.get(user_data_url, headers=headers, timeout=20)
        print(f"HTTP Status: {res.status_code}")
        data = res.json()
        status_code = data.get("status_code")
        status_msg = data.get("status_message")
        print(f"DataForSEO Status: {status_code} ({status_msg})")
        if status_code == 20000:
            tasks = data.get("tasks", [])
            if tasks and tasks[0].get("result"):
                result = tasks[0]["result"][0]
                login = result.get("login", "N/A")
                money_info = result.get("money", {})
                balance = money_info.get("balance") if isinstance(money_info, dict) else result.get("money")
                currency = result.get("currency", "USD")
                print(f"[OK] Logged in as: {login}")
                print(f"[OK] Account Balance: {balance} {currency}")
        else:
            print(f"[!] Response: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"[!] Error: {e}")

    # Test 2: Live SERP Test
    print("\n--- Test 2: Testing Live Google SERP Query ---")
    serp_url = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"
    payload = [{
        "keyword": "Monzo Bank official website",
        "language_code": "en",
        "depth": 5,
        "tag": "Monzo"
    }]

    try:
        res = requests.post(serp_url, headers=headers, json=payload, timeout=30)
        print(f"HTTP Status: {res.status_code}")
        data = res.json()
        status_code = data.get("status_code")
        status_msg = data.get("status_message")
        print(f"DataForSEO Status: {status_code} ({status_msg})")
        
        if status_code == 20000:
            tasks = data.get("tasks", [])
            if tasks and tasks[0].get("result"):
                items = tasks[0]["result"][0].get("items", [])
                print(f"[OK] Live SERP Returned {len(items)} items successfully!")
                for idx, item in enumerate(items[:3], 1):
                    print(f"  {idx}. [{item.get('type')}] {item.get('title')} -> {item.get('url')}")
            else:
                print(f"[!] No items returned in result.")
        else:
            print(f"[!] Response: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    key = "bWFuaWthbUBibGF6bHkuYWk6MGM3OWU5NmE5Mzg2ODQ5ZQ=="
    test_custom_key(key)
