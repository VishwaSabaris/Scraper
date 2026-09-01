# Multi-Platform Job Scraper & Company Website Intelligence Suite

A modular, high-performance job scraping and intelligence tool that extracts job postings across multiple global platforms, automates proxy rotation & health checking, and resolves official company websites.

---

## 🌟 Features

- **Multi-Platform Support**: Scrapers tailored for top tech and general job boards:
  - **LinkedIn** (`linkedin_scraper.py`)
  - **Indeed** (`indeed_scraper.py`)
  - **Glassdoor** (`glassdoor_scraper.py`)
  - **Reed.co.uk** (`reed_scraper.py`)
  - **ZipRecruiter** (`ziprecruiter_scraper.py`)
  - **Himalayas** (`himalayas_scraper.py`)
  - **Remote.co / Remote** (`remote_scraper.py`)
  - **JobLeads** (`jobleads_scraper.py`)
  - **Wellfound / AngelList** (`wellfound_scraper.py`)
  - **Workable** (`workable_scraper.py`)
  - **WorkAtAStartup** (`workatastartup_scraper.py`)
  - **Jobspresso** (`jobspresso_scraper.py`)
  - **Jooble** (`jooble_scraper.py`)
  - **Naukri** (`naukri_scraper.py`)
  - **CareerBuilder** (`careerbuilder_scraper.py`)
- **Automated Proxy Rotation & Health Checking**:
  - `proxy_manager.py` & `proxy_refresher.py` continuously validate, score latency, and rotate proxies to prevent rate limiting and IP blocks.
  - Multi-threaded proxy latency verification.
- **Company Website Resolver**:
  - `find_company_websites.py`: Automated company domain resolution with multi-engine fallback and domain exclusions.
- **Stealth & Anti-Bot Bypass**:
  - Playwright stealth automation, browser context isolation, and custom headers.

---

## 📁 Project Structure

```
├── .env.example                     # Environment configuration template
├── .gitignore                        # Git exclusion rules
├── requirements.txt                  # Python dependencies
├── proxy_manager.py                  # Proxy management & rotation logic
├── proxy_refresher.py                # Background proxy crawler & health-checker
├── request_client.py                 # Resilient HTTP request client
├── find_company_websites.py          # Resolves official company domains
├── find_company_websites_playwright.py
├── scrape_filtered_jobs.py           # Unified runner for filtered job search
├── utils.py                          # Common extraction and parsing utilities
│
├── [scrapers]
│   ├── linkedin_scraper.py
│   ├── indeed_scraper.py
│   ├── glassdoor_scraper.py
│   ├── reed_scraper.py
│   ├── ziprecruiter_scraper.py
│   ├── himalayas_scraper.py
│   ├── remote_scraper.py
│   ├── wellfound_scraper.py
│   ├── workable_scraper.py
│   ├── ...
│
├── data/                             # Scraped CSV datasets & proxy lists
└── scripts/                          # Proxy testing and utility scripts
```

---

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.10+
- Git

### 2. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>

python -m venv venv
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

### 3. Environment Configuration

Copy the example configuration:

```bash
cp .env.example .env
```

Adjust the proxy and API configuration inside `.env` as needed.

---

## 🛠️ Usage

### Run Job Scrapers
```bash
# Run filtered job extraction
python scrape_filtered_jobs.py

# Or run individual platform scrapers directly:
python linkedin_scraper.py
python indeed_scraper.py
python glassdoor_scraper.py
```

### Resolve Company Websites
```bash
python find_company_websites.py
```

### Test Proxy Health
```bash
python test_proxy_rotation.py
```

---

## 🔒 Security & Privacy

- Keep your `.env` file private and never commit credentials or API keys.
- Browser profiles and session data (`*_session/`) are ignored by `.env` / `.gitignore` to avoid leaking session cookies.

---

## 📄 License

MIT License
