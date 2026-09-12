import os
import sys
import base64
import json
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from find_company_websites import get_env_variable, get_dataforseo_auth_header

def test_dataforseo():
    api_key = get_env_variable("API_KEY_SERP")
    print(f"[*] Checking API_KEY_SERP...")
    if not api_key:
        print("[!] Error: API_KEY_SERP is empty or not found in .env!")
        return

    masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
    print(f"[*] Found API_KEY_SERP: {masked_key} (length: {len(api_key)})")

    auth_header = get_dataforseo_auth_header(api_key)
    print(f"[*] Generated Auth Header: {auth_header[:15]}...")

    headers = {
        "Authorization": auth_header,
        "Content-Type": "application/json"
    }

    # Test 1: User data & balance endpoint
    print("\n--- Test 1: Checking Account User Data / Balance ---")
    user_data_url = "https://api.dataforseo.com/v3/appendix/user_data"
    try:
        res = requests.get(user_data_url, headers=headers, timeout=20)
        print(f"HTTP Status: {res.status_code}")
        try:
            data = res.json()
            status_code = data.get("status_code")
            status_msg = data.get("status_message")
            print(f"DataForSEO Status: {status_code} ({status_msg})")
            
            if status_code == 20000:
                tasks = data.get("tasks", [])
                if tasks and tasks[0].get("result"):
                    result = tasks[0]["result"][0]
                    login = result.get("login", "N/A")
                    money = result.get("money", 0)
                    currency = result.get("currency", "USD")
                    print(f"[✓] Account Login: {login}")
                    print(f"[✓] Account Balance: {money} {currency}")
            else:
                print(f"[!] User Data Response: {json.dumps(data, indent=2)}")
        except Exception as e:
            print(f"Failed to parse JSON response: {e}\nRaw: {res.text}")
    except Exception as e:
        print(f"[!] Request error: {e}")

    # Test 2: Live SERP test
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
        try:
            data = res.json()
            status_code = data.get("status_code")
            status_msg = data.get("status_message")
            print(f"DataForSEO Status: {status_code} ({status_msg})")
            
            if status_code == 20000:
                tasks = data.get("tasks", [])
                if tasks and tasks[0].get("result"):
                    items = tasks[0]["result"][0].get("items", [])
                    print(f"[✓] Live SERP Returned {len(items)} items:")
                    for item in items[:3]:
                        print(f"    - Type: {item.get('type')}, URL: {item.get('url')}, Title: {item.get('title')}")
                else:
                    print(f"[!] No result items returned in task.")
            else:
                print(f"[!] SERP Task Response: {json.dumps(data, indent=2)}")
        except Exception as e:
            print(f"Failed to parse JSON response: {e}\nRaw: {res.text}")
    except Exception as e:
        print(f"[!] Request error: {e}")

if __name__ == "__main__":
    test_dataforseo()
