"""
Standalone Proxy Health Checker Script
======================================
Validates raw proxy endpoints from a source file concurrently against a test target
and saves confirmed healthy proxies to a output list file.

Usage:
    python scripts/check_proxies.py
"""

import os
import sys
import time
import logging
import asyncio
from typing import List, Optional, Tuple

# Ensure root folder is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import requests
from proxy_manager import (
    ProxyManager,
    get_config_str,
    get_config_int,
    load_env_file,
)

# Load environment configuration
load_env_file()

# Configure logger
logger = logging.getLogger("ProxyChecker")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def validate_single_proxy(
    proxy_item: dict, test_url: str, timeout: int
) -> Tuple[Optional[str], float]:
    """
    Synchronously tests a single proxy endpoint against the target test URL.
    Returns (proxy_url, latency_seconds) if valid, or (None, 0.0) if invalid.
    """
    formatted_url = proxy_item["url"]
    proxies = {"http": formatted_url, "https": formatted_url}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    start_time = time.time()
    try:
        response = requests.get(test_url, proxies=proxies, headers=headers, timeout=timeout)
        latency = time.time() - start_time
        if response.status_code == 200:
            logger.info(f"[+] Working Proxy: {proxy_item['raw']} | Latency: {latency:.2f}s")
            return formatted_url, latency
        else:
            logger.debug(f"[-] Proxy {proxy_item['raw']} returned status code {response.status_code}")
            return None, 0.0
    except (
        requests.exceptions.ProxyError,
        requests.exceptions.ConnectTimeout,
        requests.exceptions.ReadTimeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.SSLError,
    ) as err:
        logger.debug(f"[-] Proxy {proxy_item['raw']} failed check: {err}")
        return None, 0.0
    except requests.exceptions.RequestException as err:
        logger.debug(f"[-] Proxy {proxy_item['raw']} error: {err}")
        return None, 0.0


async def check_proxy_task(
    proxy_item: dict, test_url: str, timeout: int, semaphore: asyncio.Semaphore
) -> Tuple[Optional[str], float]:
    """Async task wrapper using asyncio.Semaphore to throttle concurrency."""
    async with semaphore:
        return await asyncio.to_thread(validate_single_proxy, proxy_item, test_url, timeout)


async def main():
    raw_file = get_config_str("PROXY_RAW_FILE", "data/proxylist.txt")
    valid_file = get_config_str("PROXY_LIST_FILE", "data/valid_proxies.txt")
    test_url = get_config_str("PROXY_TEST_URL", "http://httpbin.org/ip")
    concurrency = get_config_int("PROXY_CHECK_CONCURRENCY", 10)
    timeout = get_config_int("PROXY_TIMEOUT", 10)

    print("==================================================")
    print("           STANDALONE PROXY HEALTH CHECKER        ")
    print("==================================================")
    print(f"[*] Input Raw Proxy File : {raw_file}")
    print(f"[*] Output Valid File    : {valid_file}")
    print(f"[*] Test Endpoint        : {test_url}")
    print(f"[*] Max Concurrency      : {concurrency}")
    print(f"[*] Request Timeout      : {timeout}s")
    print("==================================================\n")

    if not os.path.exists(raw_file):
        logger.error(f"Raw proxy file '{raw_file}' does not exist. Please create it and populate raw proxies.")
        return

    raw_lines = []
    with open(raw_file, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    parsed_proxies = []
    seen = set()
    for line in raw_lines:
        item = ProxyManager.parse_proxy_string(line)
        if item and item["url"] not in seen:
            seen.add(item["url"])
            parsed_proxies.append(item)

    if not parsed_proxies:
        logger.warning(f"No valid proxy lines found in '{raw_file}'. Exiting.")
        return

    logger.info(f"Loaded {len(parsed_proxies)} unique candidate proxies to validate...")

    semaphore = asyncio.Semaphore(concurrency)
    tasks = [check_proxy_task(item, test_url, timeout, semaphore) for item in parsed_proxies]

    start_total = time.time()
    results = await asyncio.gather(*tasks)
    total_time = time.time() - start_total

    valid_proxies: List[Tuple[str, float]] = [r for r in results if r[0] is not None]

    logger.info(
        f"\n[+] Health check complete in {total_time:.2f}s! "
        f"Found {len(valid_proxies)}/{len(parsed_proxies)} healthy proxies."
    )

    # Save to valid_proxies.txt atomically
    os.makedirs(os.path.dirname(os.path.abspath(valid_file)), exist_ok=True)
    temp_valid_file = f"{valid_file}.tmp"

    try:
        with open(temp_valid_file, "w", encoding="utf-8") as f:
            f.write("# Validated proxy endpoints\n")
            for url, latency in valid_proxies:
                f.write(f"{url}\n")

        if os.path.exists(valid_file):
            os.remove(valid_file)
        os.rename(temp_valid_file, valid_file)
        logger.info(f"[+] Successfully saved {len(valid_proxies)} verified proxies to '{valid_file}'.")
    except Exception as err:
        logger.error(f"Failed to write validated proxies to file: {err}")


if __name__ == "__main__":
    asyncio.run(main())
