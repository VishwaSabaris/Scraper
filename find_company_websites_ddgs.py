"""
DDGS Company Website Resolver
=============================
Finds and validates official corporate homepages using DuckDuckGo Search (ddgs).
1. Parses & cleans company names (stripping legal suffixes, noise).
2. Searches via ddgs with multiple query strategies (official website, company, location).
3. Rigorously filters out directories, job portals, social media, news, review platforms, and ATS sites.
4. Maintains an incremental cache in data/company_websites.csv.
5. Updates the 'Company Link' / 'Website' column in scraped job datasets.
"""

import os
import sys
import re
import csv
import time
import random
import logging
import urllib.parse
from typing import List, Dict, Optional, Tuple, Set

# Fix Windows console encoding
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Suppress third-party verbose logs
logging.getLogger("ddgs").setLevel(logging.WARNING)
logging.getLogger("curl_cffi").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

try:
    from ddgs import DDGS
    from ddgs.exceptions import DDGSException
except ImportError:
    DDGS = None
    DDGSException = Exception

# ── Logging Configuration ───────────────────────────────────────────────────
logger = logging.getLogger("DDGSWebsiteFinder")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

CACHE_FILE = os.path.abspath("data/company_websites.csv")

# ── Blacklisted Domains (Job Boards, Aggregators, Directories, News, Social, ATS, Review Sites) ──
EXCLUDED_DOMAINS = {
    # Search engines
    "google.com", "google.co.in", "google.co.uk", "google.com.au", "google.de", "google.fr",
    "duckduckgo.com", "bing.com", "yahoo.com", "yandex.com", "baidu.com", "ask.com",
    "mojeek.com", "startpage.com", "brave.com", "search.brave.com", "search.yahoo.com",
    "ecosia.org", "qwant.com",
    
    # Social & Media Platforms
    "linkedin.com", "facebook.com", "twitter.com", "x.com", "instagram.com",
    "tiktok.com", "youtube.com", "pinterest.com", "reddit.com", "quora.com",
    "threads.net", "medium.com", "substack.com", "tumblr.com", "linktr.ee",
    "discord.com", "telegram.org", "whatsapp.com",
    
    # Job Portals & Aggregators
    "indeed.com", "indeed.co.in", "indeed.co.uk",
    "glassdoor.com", "glassdoor.co.in", "glassdoor.co.uk",
    "naukri.com", "naukrigulf.com", "shine.com", "foundit.in", "foundit.com",
    "instahyre.com", "internshala.com", "apna.co", "timesjobs.com", "freshersworld.com",
    "reed.co.uk", "wellfound.com", "angel.co", "jobspresso.co", "himalayas.app",
    "remote.com", "remoteok.com", "weworkremotely.com", "ziprecruiter.com", "careerbuilder.com",
    "simplyhired.com", "simplyhired.co.in", "totaljobs.com", "cv-library.co.uk",
    "adzuna.com", "adzuna.in", "adzuna.co.uk", "monster.com", "seek.com.au",
    "jooble.org", "jooble.com", "whatjobs.com", "careerjet.com", "careerjet.co.in",
    "neuvoo.com", "talent.com", "dice.com", "builtin.com", "workatastartup.com",
    "jobleads.com", "jobleads.co.uk", "techcareers.com", "efinancialcareers.com",
    
    # ATS & Job Board Engines
    "greenhouse.io", "lever.co", "workable.com", "freshteam.com", "smartrecruiters.com",
    "recruitee.com", "bamboohr.com", "ashbyhq.com", "breezy.hr", "jazzhr.com",
    "jobvite.com", "workday.com", "icims.com", "myworkdayjobs.com", "taleo.net",
    "successfactors.com", "applytojob.com", "teamtailor.com",
    
    # Business Registrars, Lead Directories, Market Intelligence
    "zaubacorp.com", "toffler.in", "falconebiz.com", "quickcompany.in", "instafinancials.com",
    "thecompanycheck.com", "company360.in", "tradeindia.com", "indiamart.com", "justdial.com",
    "sulekha.com", "yellowpages.com", "dnb.com", "zoominfo.com", "apollo.io", "lusha.com",
    "rocketreach.co", "signalhire.com", "contactout.com", "hunter.io", "clearbit.com",
    "tracxn.com", "cbinsights.com", "pitchbook.com", "dealroom.co", "f6s.com",
    "crunchbase.com", "theorg.com", "craft.co", "owler.com", "levels.fyi",
    "ycombinator.com", "companieshouse.gov.uk", "gov.uk", "gov.in", "mca.gov.in",
    "ambitionbox.com", "startupindia.gov.in", "vakilsearch.com", "indiafilings.com",
    "kanakkupillai.com", "trademarkia.com", "ipindiaonline.gov.in", "openpeeps.org",
    "listout.in", "datanyze.com",
    
    # Software Review & Directory Platforms
    "g2.com", "capterra.com", "softwareadvice.com", "getapp.com", "trustpilot.com",
    "mouthshut.com", "clutch.co", "goodfirms.co", "upcity.com", "sortlist.com",
    "designrush.com", "topdevelopers.co", "appfutura.com", "urbanpro.com", "shiksha.com",
    "collegedunia.com", "careers360.com", "zollege.in", "everydev.ai",
    
    # Code & Tech Repositories / Encyclopedias
    "wikipedia.org", "wikimedia.org", "wikihow.com", "grokipedia.com", "github.com",
    "gitlab.com", "bitbucket.org", "stackoverflow.com", "kaggle.com", "npm.js", "pypi.org",
    
    # News & Financial Outlets
    "indiatimes.com", "economictimes.indiatimes.com", "timesofindia.indiatimes.com",
    "thehindu.com", "ndtv.com", "moneycontrol.com", "livemint.com", "forbes.com",
    "techcrunch.com", "bloomberg.com", "reuters.com", "wsj.com", "business-standard.com",
    "theverge.com", "wired.com", "cnbc.com", "ft.com", "businessinsider.com", "hindustantimes.com",
    "indianexpress.com", "financialexpress.com", "zeebiz.com", "moneybhai.com",
    
    # App Stores & Hosting
    "play.google.com", "apps.apple.com", "chrome.google.com"
}

# Curated lookup dictionary for top corporate brands
KNOWN_ENTERPRISE_MAP = {
    "moengage": "https://www.moengage.com",
    "crowdstrike": "https://www.crowdstrike.com",
    "salesforce": "https://www.salesforce.com",
    "delhivery": "https://www.delhivery.com",
    "kloudfuse": "https://www.kloudfuse.com",
    "zentrades": "https://www.zentrades.io",
    "pinegap": "https://pinegap.ai",
    "pinegap.ai": "https://pinegap.ai",
    "zenstatement": "https://www.zenstatement.ai",
    "kodo": "https://www.kodo.com",
    "perennial systems": "https://www.perennialsys.com",
    "wozku": "https://www.wozku.com",
    "oliv ai": "https://www.oliv.ai",
    "ionage": "https://www.ionage.in",
    "zenskar": "https://www.zenskar.com",
    "edatabae": "https://edatabae.com",
    "cleartax": "https://www.cleartax.in",
    "cleartax for business": "https://www.cleartax.in",
    "nected": "https://www.nected.io",
    "leena ai": "https://www.leena.ai",
    "accenture": "https://www.accenture.com",
    "wipro": "https://www.wipro.com",
    "tcs": "https://www.tcs.com",
    "infosys": "https://www.infosys.com",
    "hcltech": "https://www.hcltech.com",
    "cognizant": "https://www.cognizant.com",
    "swiggy": "https://www.swiggy.com",
    "zomato": "https://www.zomato.com",
    "flipkart": "https://www.flipkart.com",
    "phonepe": "https://www.phonepe.com",
    "razorpay": "https://www.razorpay.com",
    "zerodha": "https://www.zerodha.com",
    "groww": "https://www.groww.in",
    "cred": "https://www.cred.club",
    "postman": "https://www.postman.com",
    "browserstack": "https://www.browserstack.com",
    "zepto": "https://www.zeptonow.com",
    "blinkit": "https://www.blinkit.com",
    "urban company": "https://www.urbancompany.com",
    "meesho": "https://www.meesho.com",
    "freshworks": "https://www.freshworks.com",
    "whatfix": "https://www.whatfix.com",
    "sprinklr": "https://www.sprinklr.com",
    "chargebee": "https://www.chargebee.com",
    "leadsquared": "https://www.leadsquared.com",
    "darwinbox": "https://www.darwinbox.com",
    "datadog": "https://www.datadoghq.com",
    "stripe": "https://www.stripe.com",
    "twilio": "https://www.twilio.com",
    "notion": "https://www.notion.so",
    "figma": "https://www.figma.com",
    "canva": "https://www.canva.com",
    "kinetic innovative staffing": "https://www.kineticstaff.com",
    "kinetic innovative staffing pty ltd": "https://www.kineticstaff.com",
    "salesmonk.ai": "https://www.salesmonk.ai",
    "salesmonk": "https://www.salesmonk.ai",
    "rao edusolutions": "https://raoiitmedical.com",
    "rao edusolutions private limited": "https://raoiitmedical.com",
    "asteroidx": "https://www.asteroidx.com",
    "quintype": "https://www.quintype.com",
    "quintype technologies": "https://www.quintype.com",
    "quintype technologies incorporation": "https://www.quintype.com",
    "the takeoff ai": "https://www.thetakeoff.ai",
    "tutorcloud.ai": "https://tutorcloud.ai",
    "tutorcloud": "https://tutorcloud.ai",
    "signellent": "https://www.signellent.com",
    "mareana": "https://www.mareana.com",
    "hotelogix": "https://www.hotelogix.com",
    "hotelogix india private limited": "https://www.hotelogix.com",
    "affinitiv": "https://www.affinitiv.com",
    "alertus technologies, llc": "https://www.alertus.com",
    "alertus technologies": "https://www.alertus.com",
    "lkq / keystone automotive operations": "https://www.lkqcorp.com",
    "lkq": "https://www.lkqcorp.com",
    "keystone automotive operations": "https://www.keystoneautomotive.com",
    "ulysses campos insurance agency llc": "https://www.statefarm.com",
    "synerfac technical staffing": "https://www.synerfac.com",
    "clio": "https://www.clio.com",
    "facilities management express": "https://www.gofmx.com",
    "generac": "https://www.generac.com",
    "ascera": "https://www.ascera.com",
    "planet labs": "https://www.planet.com",
    "vaco llc": "https://www.vaco.com",
    "vaco": "https://www.vaco.com",
    "worth ai": "https://www.worth.ai",
    "eab": "https://www.eab.com",
    "bbb heart of texas": "https://www.bbb.org",
    "ceros inc.": "https://www.ceros.com",
    "ceros": "https://www.ceros.com",
    "teksystems": "https://www.teksystems.com",
    "alation": "https://www.alation.com",
    "rotating machinery services": "https://www.rotatingmachinery.com",
    "choate agency": "https://www.choateagency.com",
    "jump": "https://www.jump.app",
    "equis financial": "https://www.equisfinancial.com",
    "conversion": "https://www.conversion.com",
    "guidebook": "https://www.guidebook.com",
    "toro tms": "https://www.torotms.com",
    "jeffrey hines state farm agency": "https://www.statefarm.com",
    "sv academy": "https://www.sv.academy",
    "coefficient": "https://www.coefficient.io",
    "tom james company": "https://www.tomjames.com",
    "michael page": "https://www.michaelpage.com",
    "sovos compliance": "https://www.sovos.com",
    "nana regional corporation inc": "https://www.nana.com",
    "techdigital": "https://www.techdigitalcorp.com",
    "u.s. department of justice": "https://www.justice.gov",
    "rubrik": "https://www.rubrik.com",
    "gimbal technologies": "https://www.gimbaltechnologies.com",
    "codingal": "https://www.codingal.com",
    "codingal technologies private limited": "https://www.codingal.com",
    "infynd": "https://www.infynd.com",
    "salescode.ai": "https://www.salescode.ai",
    "salescode": "https://www.salescode.ai",
    "softobiz": "https://www.softobiz.com",
    "softobiz technologies": "https://www.softobiz.com",
    "hubhopper": "https://www.hubhopper.com",
    "sj innovation": "https://www.sjinnovation.com",
    "databeat": "https://www.databeat.io",
    "clickpost": "https://www.clickpost.ai",
    "automotivemastermind": "https://www.automotivemastermind.com",
    "shurutech": "https://www.shuru.tech",
    "veeam software": "https://www.veeam.com",
    "docyt": "https://www.docyt.com",
    "ebizon": "https://www.ebizontek.com",
    "adit": "https://www.adit.com",
    "spotdraft": "https://www.spotdraft.com",
    "opengov": "https://www.opengov.com",
    "attentive.ai": "https://www.attentive.ai",
    "3 point human capital": "https://www.3pointhumancapital.com",
    "3 point human capital pvt ltd": "https://www.3pointhumancapital.com",
    "sbi payments services pvt ltd": "https://www.sbipayments.com",
    "sbi payments": "https://www.sbipayments.com",
    "aishwarya groups": "https://www.aishwaryagroup.co.in",
    "indian edu hub": "https://www.indianeduhub.com",
    "2nds commerce pvt ltd": "https://www.2nds.com",
    "2nds commerce": "https://www.2nds.com",
    "roomadda urban solutions pvt. ltd.": "https://www.roomadda.com",
    "roomadda": "https://www.roomadda.com",
    "bs talent solutions pvt ltd": "https://www.bstalentsolutions.com",
    "bs talent solutions": "https://www.bstalentsolutions.com",
    "procyon techsolutions private limited": "https://www.procyontechsolutions.com",
    "procyon techsolutions": "https://www.procyontechsolutions.com"
}


# ── Cleaning & Extraction Helpers ───────────────────────────────────────────

def clean_company_name(name: str) -> str:
    """Removes legal suffixes, punctuation, and portal metadata from company name."""
    if not name or str(name).strip().lower() in {
        "n/a", "unknown", "confidential", "jooble employer", "foundit recruiter",
        "careerbuilder employer", "indeed employer", "nan", "null", "none", ""
    }:
        return ""

    c = str(name).strip()
    
    # Strip bullet separators and parenthetical details
    if "•" in c:
        c = c.split("•")[0].strip()
    if "|" in c:
        c = c.split("|")[0].strip()

    # Repeat suffix stripping passes for multi-word corporate endings
    for _ in range(2):
        pattern = (
            r'(?i)\b('
            r'incorporation|incorporated|inc\.?|'
            r'private\s+limited|pvt\.?\s*ltd\.?|limited\.?|ltd\.?|'
            r'corporation|corp\.?|gmbh|llc|llp|pty\.?\s*ltd\.?|'
            r'co\.?|company|holdings|group|enterprises|'
            r'technologies|technology\s+solutions|technology|solutions|'
            r'software\s+private\s+limited|india\s+private\s+limited|'
            r'india\s+pvt\s+ltd|india\s+limited|services'
            r')\b'
        )
        c = re.sub(pattern, '', c)
        c = re.sub(r'[\(\)\[\]\{\}]', ' ', c)
        c = re.sub(r'\s+', ' ', c).strip(' ,.-')
    
    return c if len(c) >= 2 else str(name).strip()


def clean_location(loc: str) -> str:
    """Extracts primary city or country from location string."""
    if not loc or str(loc).strip().lower() in {"n/a", "remote", "work from home", "hybrid", "nan", "null", ""}:
        return ""
    parts = re.split(r'[,/]', str(loc))
    return parts[0].strip()


def is_valid_company_url(url: str) -> bool:
    """Checks whether URL is a valid corporate website and not in excluded domains."""
    if not url or url == "N/A" or not url.startswith("http"):
        return False
    try:
        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        if not netloc or "." not in netloc:
            return False
            
        for ex in EXCLUDED_DOMAINS:
            if netloc == ex or netloc.endswith("." + ex) or ex in netloc:
                return False
        return True
    except Exception:
        return False


def extract_base_url(url: str) -> str:
    """Normalizes URL to scheme + domain (e.g., https://example.com)."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
        return url
    except Exception:
        return url


# ── Persistent Cache Helpers ────────────────────────────────────────────────

def load_cache() -> Dict[str, str]:
    """Loads cached company -> website mappings from disk."""
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    c = row.get("Company Name", "").strip().lower()
                    u = row.get("Website URL", "").strip()
                    if c and u and u != "N/A" and is_valid_company_url(u):
                        cache[c] = u
        except Exception as e:
            logger.warning(f"Warning reading cache: {e}")
    return cache


def append_to_cache(company_raw: str, url: str):
    """Appends a newly resolved website mapping to the persistent CSV cache."""
    if not company_raw or not url or url == "N/A":
        return
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    file_exists = os.path.exists(CACHE_FILE)
    try:
        with open(CACHE_FILE, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["Company Name", "Website URL"])
            if not file_exists:
                writer.writeheader()
            writer.writerow({"Company Name": company_raw.lower().strip(), "Website URL": url})
    except Exception as e:
        logger.warning(f"Could not append to cache: {e}")


# ── DDGS Website Search Engine ──────────────────────────────────────────────

def search_company_website_ddgs(
    company_name: str,
    location: str = "",
    ddgs_instance: Optional[DDGS] = None,
    max_retries: int = 2
) -> str:
    """
    Searches DuckDuckGo for the official website of a company.
    Tries multiple query strategies in order of relevance.
    """
    if not company_name or str(company_name).strip().lower() in {
        "n/a", "unknown", "confidential", "jooble employer", "foundit recruiter",
        "careerbuilder employer", "indeed employer", "nan", "null", "none", ""
    }:
        return "N/A"

    raw_lower = company_name.strip().lower()
    clean_name = clean_company_name(company_name)
    clean_lower = clean_name.lower() if clean_name else raw_lower
    clean_loc = clean_location(location)

    # 1. Check curated enterprise map
    if raw_lower in KNOWN_ENTERPRISE_MAP:
        return KNOWN_ENTERPRISE_MAP[raw_lower]
    if clean_lower in KNOWN_ENTERPRISE_MAP:
        return KNOWN_ENTERPRISE_MAP[clean_lower]
    for k, url in KNOWN_ENTERPRISE_MAP.items():
        if len(k) > 3 and (k == clean_lower or f" {k} " in f" {clean_lower} "):
            return url

    # 2. Build multi-tiered queries
    queries = [
        f"{clean_name} official website",
        f"{clean_name} company",
        f"{raw_lower} official website"
    ]
    if clean_loc:
        queries.append(f"{clean_name} {clean_loc} official website")

    # If ddgs instance wasn't provided, create a temporary context
    local_ddgs = ddgs_instance or DDGS(timeout=12)

    for query in queries:
        for attempt in range(1, max_retries + 1):
            try:
                results = list(local_ddgs.text(query, max_results=8))
                if results:
                    for item in results:
                        href = item.get("href", "")
                        if is_valid_company_url(href):
                            base_url = extract_base_url(href)
                            return base_url
                # If query returned results but none passed domain check, break to next query
                break
            except DDGSException as de:
                err_msg = str(de).lower()
                if "no results" in err_msg:
                    break
                time.sleep(0.8 * attempt)
            except Exception as e:
                time.sleep(0.8 * attempt)

        # Politeness jitter between distinct queries for same company
        time.sleep(random.uniform(0.3, 0.5))

    return "N/A"


# ── Dataset Processing Pipeline ─────────────────────────────────────────────

def enrich_dataset_with_company_websites(
    filepath: str,
    output_filepath: Optional[str] = None,
    batch_pause: float = 0.4
) -> Tuple[int, int, int]:
    """
    Reads a CSV dataset, finds all unique companies, searches for their websites via DDGS,
    updates the 'Company Link' column, and saves the enriched dataset.
    
    Returns: (total_listings, unique_companies, resolved_websites)
    """
    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        return 0, 0, 0

    out_path = output_filepath or filepath
    logger.info(f"[*] Starting DDGS website discovery for: {filepath}")

    # Load persistent cache
    cache = load_cache()
    logger.info(f"[*] Loaded {len(cache)} existing cached company websites.")

    # Read rows
    rows = []
    fieldnames = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames) if reader.fieldnames else []
        for r in reader:
            rows.append(r)

    total_rows = len(rows)
    if total_rows == 0:
        logger.warning(f"File '{filepath}' is empty.")
        return 0, 0, 0

    # Ensure 'Company Link' column exists
    link_col = "Company Link"
    if link_col not in fieldnames:
        if "Website" in fieldnames:
            link_col = "Website"
        elif "Website URL" in fieldnames:
            link_col = "Website URL"
        else:
            fieldnames.append(link_col)

    # Collect unique company names and locations
    company_location_map: Dict[str, str] = {}
    for r in rows:
        c = r.get("Company Name", "").strip()
        loc = r.get("Location", "").strip()
        if c and c.lower() not in {"n/a", "unknown", "nan", "null", ""}:
            if c not in company_location_map:
                company_location_map[c] = loc

    unique_companies = list(company_location_map.keys())
    logger.info(f"[*] Dataset contains {total_rows} job postings across {len(unique_companies)} unique companies.")

    # Resolve company websites
    resolved_map: Dict[str, str] = {}
    newly_found_count = 0
    cached_count = 0

    # Initialize DDGS session
    with DDGS(timeout=15) as ddgs_session:
        for idx, company in enumerate(unique_companies, 1):
            c_lower = company.lower()
            clean_lower = clean_company_name(company).lower()
            loc = company_location_map.get(company, "")

            # 1. Check in-memory / disk cache first
            if c_lower in cache and is_valid_company_url(cache[c_lower]):
                resolved_map[company] = cache[c_lower]
                cached_count += 1
                continue
            if clean_lower in cache and is_valid_company_url(cache[clean_lower]):
                resolved_map[company] = cache[clean_lower]
                cached_count += 1
                continue

            # 2. Check enterprise dictionary
            if c_lower in KNOWN_ENTERPRISE_MAP:
                url = KNOWN_ENTERPRISE_MAP[c_lower]
                resolved_map[company] = url
                cache[c_lower] = url
                append_to_cache(company, url)
                cached_count += 1
                continue
            if clean_lower in KNOWN_ENTERPRISE_MAP:
                url = KNOWN_ENTERPRISE_MAP[clean_lower]
                resolved_map[company] = url
                cache[clean_lower] = url
                append_to_cache(company, url)
                cached_count += 1
                continue

            # 3. Perform DDGS Search
            url = search_company_website_ddgs(company, loc, ddgs_instance=ddgs_session)
            if url != "N/A":
                resolved_map[company] = url
                cache[c_lower] = url
                cache[clean_lower] = url
                append_to_cache(company, url)
                newly_found_count += 1
                logger.info(f"  [{idx}/{len(unique_companies)}] [DDGS] [+] {company} -> {url}")
            else:
                resolved_map[company] = "N/A"
                logger.warning(f"  [{idx}/{len(unique_companies)}] [DDGS] [-] {company} -> N/A")

            # Politeness delay
            time.sleep(random.uniform(batch_pause, batch_pause + 0.3))

    # Apply resolved websites to dataset rows and sanitize
    from utils import get_company_website, sanitize_job_record
    updated_listings_count = 0
    cleaned_rows = []
    
    canonical_headers = [
        "Job Role", "Company Name", "Location", "Date Posted",
        "Apply Link", "Company Link", "No. of Applicants",
        "Company / Job Details", "Source"
    ]
    is_job_dataset = any(h in fieldnames for h in ["Job Role", "Apply Link", "No. of Applicants"])
    
    for r in rows:
        company = r.get("Company Name", "").strip()
        current_link = r.get(link_col, "").strip()
        
        # If current link is already valid, keep it
        if current_link and current_link != "N/A" and is_valid_company_url(current_link):
            pass
        else:
            resolved_link = resolved_map.get(company, "N/A")
            if resolved_link != "N/A":
                r[link_col] = resolved_link
                updated_listings_count += 1
            else:
                r[link_col] = get_company_website(company, fallback_portal_url=r.get("Apply Link", ""))
                
        if is_job_dataset:
            clean_r = sanitize_job_record(r)
            cleaned_rows.append(clean_r)
        else:
            cleaned_rows.append(r)

    out_fieldnames = canonical_headers if is_job_dataset else fieldnames

    # Write output CSV with fallback if file is locked by Excel
    try:
        with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=out_fieldnames)
            writer.writeheader()
            writer.writerows(cleaned_rows)
    except PermissionError:
        base, ext = os.path.splitext(out_path)
        fallback_path = f"{base}_enriched{ext}"
        logger.warning(f"[!] '{out_path}' is locked by another program (e.g., Excel). Saving output to '{fallback_path}'.")
        with open(fallback_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=out_fieldnames)
            writer.writeheader()
            writer.writerows(cleaned_rows)
        out_path = fallback_path
    
    rows = cleaned_rows

    # Compute final metrics
    valid_websites_total = sum(
        1 for r in rows
        if r.get(link_col, "") and r.get(link_col, "") != "N/A" and is_valid_company_url(r.get(link_col, ""))
    )
    coverage_pct = (valid_websites_total / total_rows * 100) if total_rows > 0 else 0

    logger.info("=" * 65)
    logger.info(f"[+] DDGS Enrichment Complete for: {out_path}")
    logger.info(f"    - Total Listings in File     : {total_rows}")
    logger.info(f"    - Unique Companies Evaluated : {len(unique_companies)}")
    logger.info(f"    - Newly Discovered via DDGS  : {newly_found_count}")
    logger.info(f"    - Reused from Cache / Direct : {cached_count}")
    logger.info(f"    - Final Website Coverage     : {valid_websites_total} / {total_rows} ({coverage_pct:.1f}%)")
    logger.info("=" * 65)

    return total_rows, len(unique_companies), valid_websites_total


# ── CLI Interface ───────────────────────────────────────────────────────────

def main():
    """
    Command-line interface:
      python find_company_websites_ddgs.py [input_csv] [output_csv]
      python find_company_websites_ddgs.py --all
    """
    args = sys.argv[1:]

    if not args or args[0] == "--default":
        target_csv = "all_scraped_jobs_26_portals.csv"
        enrich_dataset_with_company_websites(target_csv)
    elif args[0] == "--all":
        # Run across main aggregated CSV files
        candidates = [
            "all_scraped_jobs_26_portals.csv",
            "all_sdr_26_jobs.csv",
            "all_jobs_vvs.csv",
            "final_verified_job_dataset.csv"
        ]
        for c in candidates:
            if os.path.exists(c):
                enrich_dataset_with_company_websites(c)
    elif len(args) == 2:
        enrich_dataset_with_company_websites(args[0], args[1])
    elif len(args) == 1:
        enrich_dataset_with_company_websites(args[0], args[0])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
