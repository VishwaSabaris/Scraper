"""
Request Client Module
=====================
Unified HTTP client wrapper for requests with automatic proxy selection,
retry handling, error tracking, and fallback to direct requests.
"""

import asyncio
import logging
from typing import Optional, Any, Dict
import requests

from proxy_manager import ProxyManager, get_default_proxy_manager

logger = logging.getLogger("RequestClient")


def execute_request(
    url: str,
    method: str = "GET",
    proxy_manager: Optional[ProxyManager] = None,
    max_retries: Optional[int] = None,
    timeout: Optional[int] = None,
    headers: Optional[Dict[str, str]] = None,
    session: Optional[requests.Session] = None,
    **kwargs: Any
) -> requests.Response:
    """
    Executes an HTTP request with automatic proxy rotation and retry support.
    
    If proxy mode is enabled and healthy proxies are available, requests are routed
    through rotated proxies. On network or proxy errors, the proxy is marked as failed
    and the request is retried with another proxy up to `max_retries` times.
    
    If proxy mode is disabled or no healthy proxies exist, a direct request is performed.
    """
    pm = proxy_manager or get_default_proxy_manager()
    retries = max_retries if max_retries is not None else pm.max_retries
    req_timeout = timeout if timeout is not None else pm.timeout

    request_func = session.request if session else requests.request

    if not pm.enabled:
        logger.debug(f"Proxy mode disabled. Executing direct {method} request to {url}")
        return request_func(method=method, url=url, timeout=req_timeout, headers=headers, **kwargs)

    last_exception = None

    for attempt in range(1, retries + 1):
        proxy_dict = pm.get_proxy(target="requests")

        if not proxy_dict:
            if not pm.fallback_direct:
                raise requests.exceptions.RequestException(
                    "No healthy proxies available in the pool and proxy fallback to direct connection is disabled (PROXY_FALLBACK_DIRECT=false)."
                )
            logger.info(f"No active proxies available. Falling back to direct request for attempt {attempt}/{retries}")
            try:
                response = request_func(method=method, url=url, timeout=req_timeout, headers=headers, **kwargs)
                return response
            except requests.exceptions.RequestException as err:
                logger.error(f"Direct request attempt {attempt} failed: {err}")
                last_exception = err
                continue

        logger.debug(f"Attempt {attempt}/{retries}: Sending {method} {url} via proxy {proxy_dict['http']}")
        try:
            response = request_func(
                method=method,
                url=url,
                proxies=proxy_dict,
                timeout=req_timeout,
                headers=headers,
                **kwargs
            )
            # Inspect status code for proxy or rate limit errors
            if response.status_code in (403, 407, 429, 502, 503, 504):
                logger.warning(
                    f"Proxy request returned HTTP status {response.status_code} via {proxy_dict['http']}. "
                    f"Marking proxy failure."
                )
                pm.mark_failure(proxy_dict)
                last_exception = requests.exceptions.HTTPError(f"HTTP {response.status_code}", response=response)
                continue

            pm.mark_success(proxy_dict)
            logger.debug(f"Request succeeded through proxy {proxy_dict['http']} (Status: {response.status_code})")
            return response

        except (
            requests.exceptions.ProxyError,
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.ChunkedEncodingError,
        ) as err:
            logger.warning(f"Proxy request failed via {proxy_dict['http']}: {err}")
            pm.mark_failure(proxy_dict)
            last_exception = err
        except requests.exceptions.RequestException as err:
            logger.warning(f"Request error via proxy {proxy_dict['http']}: {err}")
            pm.mark_failure(proxy_dict)
            last_exception = err

    logger.error(f"All {retries} request attempts failed for {url}.")
    if last_exception:
        raise last_exception
    raise requests.exceptions.RequestException(f"Failed to execute {method} request to {url} after {retries} retries.")


async def execute_async_request(
    url: str,
    method: str = "GET",
    proxy_manager: Optional[ProxyManager] = None,
    max_retries: Optional[int] = None,
    timeout: Optional[int] = None,
    headers: Optional[Dict[str, str]] = None,
    session: Optional[requests.Session] = None,
    **kwargs: Any
) -> requests.Response:
    """Asynchronous wrapper for `execute_request` using asyncio.to_thread."""
    return await asyncio.to_thread(
        execute_request,
        url=url,
        method=method,
        proxy_manager=proxy_manager,
        max_retries=max_retries,
        timeout=timeout,
        headers=headers,
        session=session,
        **kwargs
    )
