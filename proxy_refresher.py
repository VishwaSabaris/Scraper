"""
Proxy Refresher Module
======================
Background service that periodically fetches fresh proxies from the configured
source, validates them with bounded concurrency, updates valid_proxies.txt,
and reloads ProxyManager.
"""

import os
import re
import time
import logging
import threading
import requests
from typing import List, Set, Tuple, Optional, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from proxy_manager import ProxyManager

logger = logging.getLogger("ProxyRefresher")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class ProxyRefresher:
    """
    Manages the automatic fetching, validation, and hot-reloading
    of rotating proxy pools in a background daemon thread.
    """

    def __init__(self, proxy_manager: ProxyManager):
        self.proxy_manager = proxy_manager
        self.enabled = os.environ.get("PROXY_SOURCE_ENABLED", "true").lower() in ("true", "1", "yes", "on")
        try:
            self.interval = int(os.environ.get("PROXY_REFRESH_INTERVAL_SECONDS", "120"))
        except (ValueError, TypeError):
            self.interval = 120

        self.source_url = os.environ.get("PROXY_SOURCE_URL", "https://free-proxy-list.net/")
        self.raw_file = os.environ.get("PROXY_RAW_FILE", "data/proxylist.txt")
        self.valid_file = os.environ.get("PROXY_LIST_FILE", "data/valid_proxies.txt")
        self.test_url = os.environ.get("PROXY_TEST_URL", "http://api.ipify.org?format=json")
        
        try:
            self.concurrency = int(os.environ.get("PROXY_CHECK_CONCURRENCY", "10"))
        except (ValueError, TypeError):
            self.concurrency = 10

        try:
            self.timeout = int(os.environ.get("PROXY_TIMEOUT", "8"))
        except (ValueError, TypeError):
            self.timeout = 8

        try:
            self.max_latency = float(os.environ.get("PROXY_MAX_LATENCY_SECONDS", "1.5"))
        except (ValueError, TypeError):
            self.max_latency = 1.5

        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def fetch_proxy_list(self) -> List[str]:
        """
        Fetches proxies from the configured website source, normalizes,
        and returns them as a list of IP:PORT strings.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        logger.info(f"Fetching proxy list from: {self.source_url}")
        try:
            response = requests.get(self.source_url, headers=headers, timeout=15)
            if response.status_code != 200:
                logger.error(f"Failed to fetch proxy source. Status: {response.status_code}")
                return []

            # Locate the textarea with raw proxies
            # (Matches class='form-control' which is where the raw text is stored)
            if "class=\"form-control\"" in response.text or "form-control" in response.text:
                # Find all textareas
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, "html.parser")
                textarea = soup.find("textarea", class_="form-control")
                if textarea:
                    raw_text = textarea.text
                    proxies = re.findall(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}\b", raw_text)
                    if proxies:
                        # Deduplicate while preserving order
                        seen = set()
                        deduped = [p for p in proxies if not (p in seen or seen.add(p))]
                        return deduped

            logger.error("Could not parse proxy textarea from source page structure.")
            return []
        except Exception as err:
            logger.error(f"Error fetching proxy source list: {err}")
            return []

    def _atomic_write_proxylist(self, proxies: List[str]) -> Tuple[int, int]:
        """
        Atomically updates the raw proxylist.txt file.
        Returns (new_count, duplicate_count).
        """
        # Read existing entries to calculate duplicates & new proxies
        existing_raw: Set[str] = set()
        if os.path.exists(self.raw_file):
            try:
                with open(self.raw_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            existing_raw.add(line)
            except Exception as err:
                logger.warning(f"Could not read existing raw file: {err}")

        new_proxies = []
        duplicate_count = 0
        for p in proxies:
            if p in existing_raw:
                duplicate_count += 1
            else:
                new_proxies.append(p)
                existing_raw.add(p)

        temp_file = f"{self.raw_file}.tmp"
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.raw_file)), exist_ok=True)
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write("# Raw Proxy Snapshot\n")
                for p in sorted(list(existing_raw)):
                    f.write(f"{p}\n")
            
            # Atomic swap
            if os.path.exists(self.raw_file):
                os.remove(self.raw_file)
            os.rename(temp_file, self.raw_file)
        except Exception as err:
            logger.error(f"Failed to atomically write raw proxy snapshot: {err}")
            if os.path.exists(temp_file):
                os.remove(temp_file)

        return len(new_proxies), duplicate_count

    def validate_single_proxy(self, proxy_str: str) -> Optional[Tuple[str, float]]:
        """Validates a single proxy and returns the normalized proxy URL and latency if working."""
        parsed = ProxyManager.parse_proxy_string(proxy_str)
        if not parsed:
            return None

        url = parsed["url"]
        proxies_dict = {"http": url, "https": url}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

        try:
            start_time = time.perf_counter()
            response = requests.get(self.test_url, proxies=proxies_dict, headers=headers, timeout=self.timeout)
            elapsed = time.perf_counter() - start_time
            if response.status_code == 200:
                return (url, elapsed)
        except Exception:
            pass
        return None

    def refresh_once(self) -> None:
        """Runs a single synchronous proxy refresh cycle."""
        logger.info("Starting proxy refresh cycle...")
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # Fetch
        fetched = self.fetch_proxy_list()
        if not fetched:
            logger.warning("No proxies fetched during refresh. Retaining current proxy pool.")
            return

        # Snapshot raw file atomically
        new_count, duplicate_count = self._atomic_write_proxylist(fetched)

        # Validate with bounded concurrency using daemon Threads (avoids ThreadPoolExecutor atexit blocks)
        logger.info(f"Validating {len(fetched)} fetched proxies with concurrency limit of {self.concurrency}...")
        working_results: List[Tuple[str, float]] = []
        working_urls_lock = threading.Lock()

        import queue
        proxy_queue = queue.Queue()
        for p in fetched:
            proxy_queue.put(p)

        local_stop = threading.Event()

        def worker():
            while not local_stop.is_set() and not self._stop_event.is_set():
                try:
                    proxy_str = proxy_queue.get_nowait()
                except queue.Empty:
                    break

                try:
                    res = self.validate_single_proxy(proxy_str)
                    if res:
                        with working_urls_lock:
                            working_results.append(res)
                except Exception:
                    pass
                finally:
                    proxy_queue.task_done()

        # Spawn worker threads
        threads = []
        num_workers = min(self.concurrency, len(fetched))
        for i in range(num_workers):
            t = threading.Thread(target=worker, name=f"ProxyValidatorWorker-{i}")
            t.daemon = True
            t.start()
            threads.append(t)

        try:
            while any(t.is_alive() for t in threads):
                time.sleep(0.1)
        except KeyboardInterrupt:
            logger.warning("KeyboardInterrupt caught. Canceling all pending proxy validation tasks immediately...")
            local_stop.set()
            raise

        # Filter working results by maximum latency and sort by latency (lowest first)
        low_latency_results = [res for res in working_results if res[1] <= self.max_latency]
        low_latency_results.sort(key=lambda x: x[1])
        working_urls = [url for url, latency in low_latency_results]

        if low_latency_results:
            fastest_url, fastest_lat = low_latency_results[0]
            logger.info(
                f"Validation complete. Found {len(working_urls)} working low-latency proxies (<= {self.max_latency}s). "
                f"Fastest: {fastest_url} ({fastest_lat * 1000:.1f}ms)."
            )
        else:
            logger.info(f"Validation complete. Found 0 working low-latency proxies (<= {self.max_latency}s).")

        # Atomic update of valid_proxies.txt
        if not working_urls:
            logger.warning(
                "Zero working proxies found in this cycle. "
                "Retaining current valid proxy pool (valid_proxies.txt untouched)."
            )
            return

        temp_valid = f"{self.valid_file}.tmp"
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.valid_file)), exist_ok=True)
            with open(temp_valid, "w", encoding="utf-8") as f:
                f.write("# Refreshed Valid Proxies List\n")
                for url in working_urls:
                    f.write(f"{url}\n")
            
            # Atomic swap
            if os.path.exists(self.valid_file):
                os.remove(self.valid_file)
            os.rename(temp_valid, self.valid_file)
            logger.info(f"Successfully saved {len(working_urls)} validated proxies to: {self.valid_file}")
            
            # Hot reload
            self.proxy_manager.reload_proxies()
        except Exception as err:
            logger.error(f"Failed to atomically write valid proxies: {err}")
            if os.path.exists(temp_valid):
                os.remove(temp_valid)

        logger.info(
            f"Refresh cycle stats: [Fetched: {len(fetched)}] [New: {new_count}] "
            f"[Duplicates: {duplicate_count}] [Valid: {len(working_urls)}] [Time: {timestamp}]"
        )

    def _run_loop(self) -> None:
        """Background loop running the periodic refresh."""
        logger.info(f"Background proxy refresher thread started. Refresh interval: {self.interval}s.")
        # Perform initial refresh immediately on startup
        try:
            self.refresh_once()
        except Exception as err:
            logger.error(f"Error during initial refresh: {err}")

        while not self._stop_event.is_set():
            # Sleep in small increments to allow rapid shutdown response
            for _ in range(self.interval):
                if self._stop_event.is_set():
                    break
                time.sleep(1)
            
            if self._stop_event.is_set():
                break

            try:
                self.refresh_once()
            except Exception as err:
                logger.error(f"Error during periodic refresh: {err}")

        logger.info("Background proxy refresher thread stopped.")

    def start(self) -> None:
        """Starts the refresher in a background daemon thread."""
        if not self.enabled:
            logger.info("Proxy Refresher is disabled by configuration (PROXY_SOURCE_ENABLED=false).")
            return

        with self._lock:
            if self._thread and self._thread.is_alive():
                logger.warning("Proxy Refresher is already running.")
                return

            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_loop, name="ProxyRefresherThread")
            self._thread.daemon = True
            self._thread.start()

    def stop(self) -> None:
        """Stops the background refresher thread gracefully."""
        with self._lock:
            if not self._thread or not self._thread.is_alive():
                return
            logger.info("Stopping proxy refresher background service...")
            self._stop_event.set()
            # Wait for thread to stop
            self._thread.join(timeout=10)
            self._thread = None
