"""
Fetch Free Proxies Script
=========================
Programmatically pulls raw proxy IP list from https://free-proxy-list.net/
and appends them to data/proxylist.txt.

Usage:
    python scripts/fetch_free_proxies.py
"""

import os
import re
import sys
import logging
import requests
from bs4 import BeautifulSoup

# Ensure root folder is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from proxy_manager import get_config_str, load_env_file

# Load environment configuration
load_env_file()

# Configure logger
logger = logging.getLogger("ProxyFetcher")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def fetch_free_proxies():
    raw_file = get_config_str("PROXY_RAW_FILE", "data/proxylist.txt")
    url = "https://free-proxy-list.net/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    logger.info(f"Fetching free proxies from {url}...")
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            logger.error(f"Failed to fetch proxies. Status code: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        textarea = soup.find("textarea", class_="form-control")
        if not textarea:
            logger.error("Could not find raw proxy textarea on the page.")
            return

        # Find all lines matching IP:PORT pattern
        raw_text = textarea.text
        proxies = re.findall(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}\b", raw_text)

        if not proxies:
            logger.warning("No IP:PORT combinations found in the textarea.")
            return

        logger.info(f"Extracted {len(proxies)} proxies from free-proxy-list.net.")

        # Read existing proxies to avoid duplicate entries
        existing = set()
        if os.path.exists(raw_file):
            with open(raw_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        existing.add(line)

        new_count = 0
        os.makedirs(os.path.dirname(os.path.abspath(raw_file)), exist_ok=True)
        with open(raw_file, "a", encoding="utf-8") as f:
            for p in proxies:
                if p not in existing:
                    f.write(f"{p}\n")
                    existing.add(p)
                    new_count += 1

        logger.info(f"Added {new_count} new unique proxies to '{raw_file}'. Total unique raw proxies: {len(existing)}.")
        print(f"\n[+] Successfully loaded {new_count} new raw proxies into '{raw_file}'.")
        print("[*] Next, run 'python scripts/check_proxies.py' to validate them.")

    except Exception as err:
        logger.error(f"Error fetching free proxies: {err}")


if __name__ == "__main__":
    fetch_free_proxies()
