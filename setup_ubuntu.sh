#!/usr/bin/env bash
# ==============================================================================
# Automated Ubuntu Setup Script for Universal Job Scraper Suite
# Supported: Ubuntu 20.04 / 22.04 / 24.04 (Desktop, Server, WSL2, Cloud VPS)
# ==============================================================================

set -e

echo "=========================================================="
echo " [*] Step 1/5: Updating system packages and installing prerequisites..."
echo "=========================================================="
sudo apt update
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    curl \
    wget \
    build-essential \
    libffi-dev \
    libssl-dev \
    xvfb \
    ca-certificates

echo ""
echo "=========================================================="
echo " [*] Step 2/5: Creating Python virtual environment..."
echo "=========================================================="
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "[+] Virtual environment 'venv' created successfully."
else
    echo "[*] Existing virtual environment found."
fi

# Activate virtual environment
source venv/bin/activate

echo ""
echo "=========================================================="
echo " [*] Step 3/5: Installing Python package dependencies..."
echo "=========================================================="
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo ""
echo "=========================================================="
echo " [*] Step 4/5: Installing Playwright Chromium browser & OS libraries..."
echo "=========================================================="
playwright install chromium
sudo playwright install-deps

echo ""
echo "=========================================================="
echo " [++++] Step 5/5: Setup Complete!"
echo "=========================================================="
echo ""
echo "To run the scraper suite:"
echo "  1. Activate the virtual environment:"
echo "       source venv/bin/activate"
echo ""
echo "  2. Run the interactive scraper:"
echo "       python scrape_all_jobs_master.py"
echo ""
echo "  3. Or run in headless cloud/VPS mode using xvfb:"
echo "       xvfb-run -a python scrape_all_jobs_master.py --role \"DevOps Engineer\" --location \"Bangalore\" --portals \"all\""
echo ""
echo "  4. Standardize dates and resolve company websites:"
echo "       python resolve_company_websites.py all_jobs_vvs.csv"
echo "=========================================================="
