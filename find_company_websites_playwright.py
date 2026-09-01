"""
Company Website Finder — Google Search via Real Chrome (Persistent Context)
===========================================================================
Uses the existing Chrome persistent session (same pattern as other scrapers)
to search Google for company websites. Real Chrome is NOT detected as headless
and renders full search results correctly.

Extracts website URLs from Google's `cite` elements (domain breadcrumbs shown
under each result title) which are far more reliable than raw anchor hrefs.
"""

import os
import csv
import time
import random
import asyncio
import urllib.parse
import logging
from typing import List, Dict, Optional
from playwright.async_api import async_playwright

# Load stealth args from utils if available, otherwise define inline
try:
    from utils import CHROMIUM_STEALTH_ARGS, STEALTH_JS_INIT
except ImportError:
    CHROMIUM_STEALTH_ARGS = [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-infobars",
        "--window-position=0,0",
        "--ignore-certificate-errors",
        "--disable-dev-shm-usage",
    ]
    STEALTH_JS_INIT = """
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        window.chrome = { runtime: {} };
    """

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
)
logger = logging.getLogger("CompanyWebsiteFinder")

# Directories / job boards to exclude from results
EXCLUDED_DOMAINS = {
    "google.com", "google.co.uk", "google.co.in", "google.com.au",
    "linkedin.com", "indeed.com", "glassdoor.com", "glassdoor.co.uk",
    "facebook.com", "twitter.com", "instagram.com", "tiktok.com",
    "wikipedia.org", "crunchbase.com", "reed.co.uk", "wellfound.com",
    "github.com", "youtube.com", "xing.com", "zoominfo.com",
    "pitchbook.com", "jobspresso.co", "himalayas.app", "remote.com",
    "ziprecruiter.com", "careerbuilder.com", "naukri.com", "simplyhired.com",
    "totaljobs.com", "cv-library.co.uk", "adzuna.com", "monster.com",
    "seek.com.au", "glassdoor.co.uk", "bloomberg.com", "reuters.com",
}


def clean_company_name(name: str) -> str:
    """Strip common company suffixes for a cleaner search query."""
    name = name.strip()
    # Strip bullet separators like "Wise • London"
    if "•" in name:
        name = name.split("•")[0].strip()
    for suffix in [
        " Ltd", " Limited", " LLC", " Inc.", " Inc", " Corp.", " Corp",
        " Co.", " Co", " plc", " PLC", " LLP",
    ]:
        if name.endswith(suffix):
            name = name[: -len(suffix)].strip()
    return name


def clean_location(location: str) -> str:
    """Extract primary city from location string."""
    if not location:
        return ""
    # Strip trailing country / UK/US noise
    parts = [p.strip() for p in location.split(",")]
    return parts[0]


def is_valid_company_website(url: str) -> bool:
    """Return True only if the URL is an official company homepage (not a directory)."""
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        for ex in EXCLUDED_DOMAINS:
            if domain == ex or domain.endswith("." + ex):
                return False
        return True
    except Exception:
        return False


async def resolve_website(page, company: str, location: str) -> Optional[str]:
    """
    Navigates to Google search and extracts the website domain from the
    'cite' breadcrumb element under each organic result (the green/grey
    URL text shown beneath every search result title).
    Falls back to scanning <a> elements if no cite elements found.
    """
    clean_name = clean_company_name(company)
    clean_loc = clean_location(location)
    query = f'"{clean_name}" {clean_loc} official website'
    encoded_query = urllib.parse.quote_plus(query)
    search_url = f"https://www.google.com/search?q={encoded_query}"

    logger.info(f"Searching Google for '{company}' → {search_url}")

    try:
        await page.goto(search_url, timeout=25000, wait_until="domcontentloaded")
        # Let JS execute and results render
        await asyncio.sleep(random.uniform(1.5, 2.5))

        # ---------- Strategy 1: extract domains from <cite> elements ----------
        # Google renders result URLs as <cite> tags (e.g. "alchemy.us › ...")
        cites = await page.evaluate(
            """() => Array.from(document.querySelectorAll('cite')).map(c => c.innerText.trim())"""
        )
        for cite_text in cites:
            if not cite_text:
                continue
            # cite_text looks like "alchemy.us › about" — take the root domain part
            domain_part = cite_text.split("›")[0].strip().split("/")[0].strip()
            if not domain_part or "." not in domain_part:
                continue
            candidate = f"https://{domain_part}"
            if is_valid_company_website(candidate):
                logger.info(f"[cite] Found '{company}': {candidate}")
                return candidate

        # ---------- Strategy 2: scan <a> elements for organic result links ----
        hrefs = await page.evaluate(
            """() => Array.from(document.querySelectorAll('a[href]')).map(a => a.href)"""
        )
        for href in hrefs:
            if not href or not href.startswith("http"):
                continue
            if any(g in href for g in ("google.com", "google.co.", "google.com.au")):
                continue
            if is_valid_company_website(href):
                parsed = urllib.parse.urlparse(href)
                site = f"{parsed.scheme}://{parsed.netloc}"
                logger.info(f"[href] Found '{company}': {site}")
                return site

        logger.warning(f"No website found for '{company}'.")
        return None

    except Exception as err:
        logger.error(f"Error searching '{company}': {err}")
        return None


async def main():
    input_csv = "linkedin_jobs.csv"
    output_csv = "data/company_websites.csv"
    session_dir = os.path.abspath("./google_search_session")

    if not os.path.exists(input_csv):
        logger.error(f"Input CSV '{input_csv}' not found.")
        return

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    os.makedirs(session_dir, exist_ok=True)

    # ── 1. Read unique companies ──────────────────────────────────────────────
    unique_companies: List[Dict[str, str]] = []
    seen: set = set()
    with open(input_csv, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            company = row.get("Company Name", "").strip()
            location = row.get("Location", "").strip()
            if company and company.lower() != "n/a":
                key = (company.lower(), location.lower())
                if key not in seen:
                    seen.add(key)
                    unique_companies.append({"Company Name": company, "Location": location})

    logger.info(f"Loaded {len(unique_companies)} unique companies.")

    # ── 2. Load already-resolved entries (skip N/A, keep good URLs) ──────────
    existing: Dict[str, str] = {}
    if os.path.exists(output_csv):
        try:
            with open(output_csv, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    c = row.get("Company Name", "").strip().lower()
                    url = row.get("Website URL", "").strip()
                    if url and url != "N/A":
                        existing[c] = url
            logger.info(f"Pre-loaded {len(existing)} already-resolved websites.")
        except Exception as e:
            logger.warning(f"Could not read existing mapping: {e}")

    # ── 3. Launch real Chrome via persistent context ──────────────────────────
    async with async_playwright() as p:
        logger.info("Launching Chrome persistent context for Google Search…")
        try:
            context = await p.chromium.launch_persistent_context(
                session_dir,
                headless=False,
                channel="chrome",          # real Chrome, not Chromium bundle
                args=CHROMIUM_STEALTH_ARGS,
                viewport={"width": 1366, "height": 768},
            )
        except Exception:
            logger.warning("Real Chrome unavailable, falling back to bundled Chromium.")
            context = await p.chromium.launch_persistent_context(
                session_dir,
                headless=False,
                args=CHROMIUM_STEALTH_ARGS,
                viewport={"width": 1366, "height": 768},
            )

        await context.add_init_script(STEALTH_JS_INIT)
        page = context.pages[0] if context.pages else await context.new_page()

        # Warm up — visit Google homepage first
        try:
            await page.goto("https://www.google.com", timeout=15000)
            await asyncio.sleep(2)
        except Exception:
            pass

        temp_results: List[Dict[str, str]] = []
        resolved_count = 0
        total = len(unique_companies)

        for idx, entry in enumerate(unique_companies, 1):
            company = entry["Company Name"]
            location = entry["Location"]

            if company.lower() in existing:
                website = existing[company.lower()]
                logger.info(f"[{idx}/{total}] Skipping '{company}' → already resolved: {website}")
            else:
                website = await resolve_website(page, company, location)
                if website:
                    resolved_count += 1
                    existing[company.lower()] = website
                else:
                    website = "N/A"

                # Polite delay between searches (1.5–3 s)
                await asyncio.sleep(random.uniform(1.5, 3.0))

            temp_results.append({
                "Company Name": company,
                "Location": location,
                "Website URL": website,
            })

        await context.close()

    # ── 4. Write full consolidated output ─────────────────────────────────────
    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Company Name", "Location", "Website URL"])
        writer.writeheader()
        writer.writerows(temp_results)

    logger.info(
        f"Done. Resolved {resolved_count} new websites. "
        f"Full dataset ({len(temp_results)} rows) saved to '{output_csv}'."
    )


if __name__ == "__main__":
    asyncio.run(main())
