# Universal 26-Platform Job Scraper & Intelligence Suite

An enterprise-grade, high-performance job scraping, dynamic filtering, and corporate intelligence suite. It extracts job postings across **26 global and Indian job portals**, automatically adapts query filters, omits unsupported parameters gracefully, standardizes dates, enriches job descriptions/skills, and resolves official corporate websites.

---

## 🌟 Features

- **Universal 26-Portal Coverage**:
  - **Indian Job Boards**: Foundit (Monster India), Apna.co, Instahyre, Internshala, Shine, TimesJobs, Freshersworld, Naukri.
  - **Global & Tech Job Boards**: LinkedIn, Indeed, Glassdoor, Reed.co.uk, BuiltIn, Careerjet, Dice, SimplyHired, CareerBuilder, Jooble, JobLeads, Himalayas, Wellfound (AngelList), Remote.co / Remote, Workable, WorkAtAStartup, ZipRecruiter, Jobspresso.
- **Dynamic Filter Adaptation Engine** (`filter_engine.py`):
  - Automatically translates search filters (role, location, work mode, experience, salary, freshness, job type, skills, company) into native portal parameters.
  - Gracefully omits unsupported parameters per portal while logging actions.
- **Interactive Multi-Portal Master Runner** (`scrape_all_jobs_master.py`):
  - Interactive CLI prompt with guided questionnaire or non-interactive flag execution.
  - Multi-page uncapped pagination with concurrency controls.
- **Universal Date Standardizer** (`utils.py`):
  - Automatically normalizes 13-digit Unix millisecond epoch timestamps, relative strings (`"30+ days ago"`), and ISO UTC dates into clean ISO `YYYY-MM-DD`.
- **Enterprise Company Website Resolver** (`resolve_company_websites.py` & `find_company_websites.py`):
  - High-speed domain resolution engine with curated corporate mapping and persistent disk caching (`data/company_websites.csv`).
- **Automated Proxy Rotation & Health Checking**:
  - `proxy_manager.py` & `proxy_refresher.py` continuously validate, score latency, and rotate proxies to prevent rate limiting and IP blocks.
- **Stealth & Anti-Bot Protection**:
  - Playwright stealth automation, browser context isolation, TLS browser impersonation (`curl_cffi`), and custom browser headers.

---

## 📁 Project Structure

```
├── filter_engine.py                 # Dynamic filter translation & capability matrix
├── scrape_all_jobs_master.py        # Master 26-portal interactive/CLI runner
├── resolve_company_websites.py      # High-speed company website resolver & date normalizer
├── find_company_websites.py         # Secondary company domain discovery engine
├── utils.py                         # Universal date normalizer, stealth headers, role matchers
├── proxy_manager.py                 # Multi-threaded proxy rotation & scoring
├── proxy_refresher.py               # Background proxy harvester & health checker
├── request_client.py                # Resilient HTTP request client with retry logic
├── requirements.txt                 # Python dependencies
├── .gitignore                       # Git exclusions
│
├── [Portal Scrapers]
│   ├── foundit_scraper.py
│   ├── apna_scraper.py
│   ├── instahyre_scraper.py
│   ├── internshala_scraper.py
│   ├── shine_scraper.py
│   ├── adzuna_scraper.py
│   ├── builtin_scraper.py
│   ├── careerjet_scraper.py
│   ├── dice_scraper.py
│   ├── simplyhired_scraper.py
│   ├── timesjobs_scraper.py
│   ├── freshersworld_scraper.py
│   ├── linkedin_scraper.py
│   ├── indeed_scraper.py
│   ├── glassdoor_scraper.py
│   ├── reed_scraper.py
│   ├── naukri_scraper.py
│   ├── careerbuilder_scraper.py
│   ├── jooble_scraper.py
│   ├── jobleads_scraper.py
│   ├── himalayas_scraper.py
│   ├── remote_scraper.py
│   ├── wellfound_scraper.py
│   ├── workable_scraper.py
│   ├── ziprecruiter_scraper.py
│   └── jobspresso_scraper.py
│
├── data/                            # Datasets, company website cache & proxy lists
│   ├── company_websites.csv         # Persistent resolved corporate domains
│   └── low_latency_proxies.txt      # Verified fast proxies
└── scratch/                         # Analysis scripts and verification tools
```

---

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.10+
- Git

### 2. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/VishwaSabaris/Scraper.git
cd Scraper

python -m venv venv
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

---

## 🛠️ Usage

### 1. Interactive Master Job Search (Recommended)
Run the guided questionnaire prompt:
```bash
python scrape_all_jobs_master.py
```
This lets you select target portals (`all`, `indian`, `global`, or custom), work mode, experience level, salary, freshness, and max pages.

### 2. CLI Automated Execution
```bash
python scrape_all_jobs_master.py \
    --role "DevOps Engineer" \
    --location "Bangalore" \
    --work-mode "remote" \
    --freshness 7 \
    --portals "foundit,apna,instahyre,shine,timesjobs,dice" \
    --pages 3 \
    --output "devops_jobs.csv"
```

### 3. Standardize Dates & Resolve Company Websites
```bash
python resolve_company_websites.py all_jobs_vvs.csv
```

---

## 🔒 Security & Privacy

- Sensitive credentials and `.env` files are excluded via `.gitignore`.
- Playwright user profiles and session directories (`*_session/`) are automatically ignored.

---

## 📄 License

MIT License
