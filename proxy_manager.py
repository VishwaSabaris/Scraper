"""
Proxy Manager Module
====================
Provides thread-safe and async-safe proxy loading, round-robin rotation,
health tracking, cooldown periods, format normalization, and configuration.
"""

import os
import re
import time
import logging
import threading
from typing import List, Dict, Any, Optional, Union

# Configure logger
logger = logging.getLogger("ProxyManager")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def load_env_file(filepath: str = ".env") -> None:
    """Reads a local .env file into os.environ if it exists."""
    if not os.path.exists(filepath):
        return
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key and key not in os.environ:
                        os.environ[key] = val
    except Exception as err:
        logger.warning(f"Error loading .env file from {filepath}: {err}")


# Auto-load environment variables from .env if present
load_env_file()


def get_config_bool(key: str, default: bool) -> bool:
    val = os.environ.get(key, "").lower()
    if val in ("true", "1", "yes", "on"):
        return True
    elif val in ("false", "0", "no", "off"):
        return False
    return default


def get_config_int(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key, default))
    except (ValueError, TypeError):
        return default


def get_config_str(key: str, default: str) -> str:
    return os.environ.get(key, default).strip()


class ProxyManager:
    """
    Manages loading, rotation, health checking, failure tracking, and cooldowns
    for proxy endpoints across HTTP requests.
    """

    def __init__(self, proxy_file: Optional[str] = None, enabled: Optional[bool] = None):
        self.enabled = enabled if enabled is not None else get_config_bool("PROXY_ENABLED", True)
        self.proxy_file = proxy_file or get_config_str("PROXY_LIST_FILE", "data/valid_proxies.txt")
        self.failure_threshold = get_config_int("PROXY_FAILURE_THRESHOLD", 3)
        self.cooldown_seconds = get_config_int("PROXY_COOLDOWN_SECONDS", 300)
        self.timeout = get_config_int("PROXY_TIMEOUT", 10)
        self.max_retries = get_config_int("PROXY_MAX_RETRIES", 3)
        self.fallback_direct = get_config_bool("PROXY_FALLBACK_DIRECT", False)

        self._lock = threading.Lock()
        self._proxies: List[Dict[str, Any]] = []
        self._counter = 0

        if self.enabled:
            self.reload_proxies()

    @staticmethod
    def parse_proxy_string(raw_line: str) -> Optional[Dict[str, Any]]:
        """
        Parses and validates a proxy string.
        Supported formats:
        - IP:PORT
        - http://IP:PORT
        - https://IP:PORT
        - user:pass@IP:PORT
        - http://user:pass@IP:PORT
        """
        line = raw_line.strip()
        if not line or line.startswith("#"):
            return None

        # Remove scheme if present
        scheme = "http"
        if "://" in line:
            scheme, line = line.split("://", 1)
            scheme = scheme.lower()

        username = None
        password = None
        if "@" in line:
            auth_part, line = line.rsplit("@", 1)
            if ":" in auth_part:
                username, password = auth_part.split(":", 1)
            else:
                username = auth_part

        if ":" not in line:
            return None

        host, port_str = line.rsplit(":", 1)
        try:
            port = int(port_str)
            if not (1 <= port <= 65535):
                return None
        except ValueError:
            return None

        if not host:
            return None

        # Construct normalized URL
        if username and password:
            formatted_url = f"{scheme}://{username}:{password}@{host}:{port}"
        elif username:
            formatted_url = f"{scheme}://{username}@{host}:{port}"
        else:
            formatted_url = f"{scheme}://{host}:{port}"

        return {
            "raw": line,
            "url": formatted_url,
            "scheme": scheme,
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "success_count": 0,
            "failure_count": 0,
            "disabled_until": None,
        }

    def reload_proxies(self) -> int:
        """Loads and parses proxies from the configured proxy file."""
        with self._lock:
            if not os.path.exists(self.proxy_file):
                logger.warning(f"Proxy file not found: '{self.proxy_file}'. Proxy mode active without pool.")
                self._proxies = []
                return 0

            existing_meta = {p["url"]: (p["success_count"], p["failure_count"], p["disabled_until"]) for p in self._proxies}
            new_proxies = []
            seen_urls = set()

            try:
                with open(self.proxy_file, "r", encoding="utf-8") as f:
                    for line in f:
                        parsed = self.parse_proxy_string(line)
                        if parsed and parsed["url"] not in seen_urls:
                            seen_urls.add(parsed["url"])
                            url = parsed["url"]
                            if url in existing_meta:
                                sc, fc, du = existing_meta[url]
                                parsed["success_count"] = sc
                                parsed["failure_count"] = fc
                                parsed["disabled_until"] = du
                            new_proxies.append(parsed)
            except Exception as err:
                logger.error(f"Failed to read proxy file '{self.proxy_file}': {err}")

            self._proxies = new_proxies
            logger.info(f"Loaded {len(self._proxies)} unique valid proxies from '{self.proxy_file}'.")
            return len(self._proxies)

    def get_proxy(self, target: str = "requests") -> Optional[Union[Dict[str, str], str]]:
        """
        Returns the next healthy rotated proxy formatted for the specified library/framework.
        Options for target:
        - 'requests': dict {'http': url, 'https': url}
        - 'playwright': dict {'server': url, 'username': ..., 'password': ...}
        - 'raw': string url
        - 'dict': internal proxy metadata dict
        """
        if not self.enabled:
            return None

        with self._lock:
            if not self._proxies:
                logger.warning("Proxy pool is currently empty.")
                return None

            now = time.time()
            available = []

            for p in self._proxies:
                if p["disabled_until"] is not None:
                    if now >= p["disabled_until"]:
                        # Cooldown expired, re-enable proxy
                        logger.info(f"Proxy cooldown expired for {p['host']}:{p['port']}. Re-enabling proxy.")
                        p["disabled_until"] = None
                        p["failure_count"] = 0
                        available.append(p)
                else:
                    available.append(p)

            if not available:
                logger.warning("No healthy proxies available (all proxies are currently in cooldown).")
                return None

            selected = available[self._counter % len(available)]
            self._counter += 1

            url = selected["url"]
            logger.debug(f"Selected proxy {selected['host']}:{selected['port']} for target '{target}'.")

            if target == "requests":
                return {"http": url, "https": url}
            elif target == "playwright":
                pw_dict = {"server": f"{selected['scheme']}://{selected['host']}:{selected['port']}"}
                if selected["username"]:
                    pw_dict["username"] = selected["username"]
                if selected["password"]:
                    pw_dict["password"] = selected["password"]
                return pw_dict
            elif target == "dict":
                return selected
            else:
                return url

    def mark_success(self, proxy: Union[str, Dict[str, Any]]) -> None:
        """Marks a proxy as successful and resets its failure count."""
        if not proxy:
            return

        target_url = self._extract_url(proxy)
        if not target_url:
            return

        with self._lock:
            for p in self._proxies:
                if p["url"] == target_url or p["raw"] in target_url:
                    p["success_count"] += 1
                    p["failure_count"] = 0
                    logger.debug(f"Proxy success recorded: {p['host']}:{p['port']} (total success: {p['success_count']})")
                    break

    def mark_failure(self, proxy: Union[str, Dict[str, Any]]) -> None:
        """Marks a proxy as failed and temporarily disables it if failure threshold is reached."""
        if not proxy:
            return

        target_url = self._extract_url(proxy)
        if not target_url:
            return

        with self._lock:
            for p in self._proxies:
                if p["url"] == target_url or p["raw"] in target_url:
                    p["failure_count"] += 1
                    logger.warning(
                        f"Proxy request failed: {p['host']}:{p['port']} "
                        f"(consecutive failures: {p['failure_count']}/{self.failure_threshold})"
                    )

                    if p["failure_count"] >= self.failure_threshold:
                        p["disabled_until"] = time.time() + self.cooldown_seconds
                        logger.warning(
                            f"Proxy temporarily disabled: {p['host']}:{p['port']} "
                            f"for {self.cooldown_seconds}s (until {time.strftime('%H:%M:%S', time.localtime(p['disabled_until']))})"
                        )
                    break

    @staticmethod
    def _extract_url(proxy: Union[str, Dict[str, Any]]) -> Optional[str]:
        if isinstance(proxy, str):
            return proxy
        elif isinstance(proxy, dict):
            if "url" in proxy:
                return proxy["url"]
            elif "http" in proxy:
                return proxy["http"]
            elif "server" in proxy:
                return proxy["server"]
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics about the current proxy pool."""
        with self._lock:
            total = len(self._proxies)
            now = time.time()
            disabled = sum(1 for p in self._proxies if p["disabled_until"] and p["disabled_until"] > now)
            active = total - disabled
            return {
                "total": total,
                "active": active,
                "disabled": disabled,
                "enabled": self.enabled,
            }


_DEFAULT_PROXY_MANAGER: Optional[ProxyManager] = None


def get_default_proxy_manager() -> ProxyManager:
    """Singleton getter for the default global ProxyManager instance."""
    global _DEFAULT_PROXY_MANAGER
    if _DEFAULT_PROXY_MANAGER is None:
        _DEFAULT_PROXY_MANAGER = ProxyManager()
    return _DEFAULT_PROXY_MANAGER
