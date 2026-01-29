#!/bin/bash
#
# Upgrade taco's Python environment to match churro
#
# Problem: taco has Python 3.10 + numpy 1.26, churro has Python 3.12 + numpy 2.3
# Checkpoints created on churro can't be loaded on taco due to numpy pickle incompatibility
#
# This script:
# 1. Installs Python 3.12 on taco
# 2. Backs up the old venv
# 3. Creates a new venv with Python 3.12
# 4. Installs packages from churro's requirements
# 5. Restarts supervisor
#
# Run this script ON TACO as root:
#   sudo bash /sphere/app/upgrade-taco-python312.sh
#

set -e

echo "========================================================================"
echo "TACO PYTHON 3.12 UPGRADE SCRIPT"
echo "========================================================================"
echo ""

# Check we're running on taco
HOSTNAME=$(hostname)
if [[ ! "$HOSTNAME" =~ "taco" ]]; then
    echo "WARNING: This script is intended for taco, but running on: $HOSTNAME"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# Check we're root
if [[ $EUID -ne 0 ]]; then
    echo "ERROR: This script must be run as root (sudo)"
    exit 1
fi

echo "Step 1: Adding deadsnakes PPA and installing Python 3.12..."
echo "------------------------------------------------------------------------"
# Ubuntu 22.04 doesn't have Python 3.12 in default repos - need deadsnakes PPA
apt update
apt install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt update
apt install -y python3.12 python3.12-venv python3.12-dev

# Verify installation
if ! command -v python3.12 &> /dev/null; then
    echo "ERROR: python3.12 installation failed"
    exit 1
fi
echo "Python 3.12 installed: $(python3.12 --version)"
echo ""

echo "Step 2: Stopping supervisor services..."
echo "------------------------------------------------------------------------"
supervisorctl stop all || true
echo ""

echo "Step 3: Backing up current venv..."
echo "------------------------------------------------------------------------"
BACKUP_DIR="/sphere/.venv-backup-py310-$(date +%Y%m%d-%H%M%S)"
if [[ -d /sphere/.venv ]]; then
    echo "Moving /sphere/.venv to $BACKUP_DIR"
    mv /sphere/.venv "$BACKUP_DIR"
    echo "Backup created at: $BACKUP_DIR"
else
    echo "No existing venv found at /sphere/.venv"
fi
echo ""

echo "Step 4: Getting requirements from churro..."
echo "------------------------------------------------------------------------"
RAW_REQUIREMENTS="/tmp/churro-requirements-raw-$(date +%Y%m%d-%H%M%S).txt"
REQUIREMENTS_FILE="/tmp/churro-requirements-$(date +%Y%m%d-%H%M%S).txt"

# Try churro.local first (mDNS), fall back to churro
echo "Fetching pip freeze from churro..."
if ssh -o ConnectTimeout=5 churro.local "source /sphere/.venv/bin/activate && pip freeze" > "$RAW_REQUIREMENTS" 2>/dev/null; then
    echo "Connected via churro.local"
elif ssh -o ConnectTimeout=5 churro "source /sphere/.venv/bin/activate && pip freeze" > "$RAW_REQUIREMENTS" 2>/dev/null; then
    echo "Connected via churro"
else
    echo "ERROR: Could not connect to churro or churro.local"
    exit 1
fi

# Filter out featrix-* packages (installed from internal PyPI, not public)
grep -v "^featrix" "$RAW_REQUIREMENTS" > "$REQUIREMENTS_FILE"

TOTAL_COUNT=$(wc -l < "$RAW_REQUIREMENTS")
FILTERED_COUNT=$(wc -l < "$REQUIREMENTS_FILE")
FEATRIX_COUNT=$((TOTAL_COUNT - FILTERED_COUNT))
echo "Retrieved $TOTAL_COUNT packages from churro"
echo "Filtered out $FEATRIX_COUNT featrix-* packages (will install separately)"
echo "Requirements saved to: $REQUIREMENTS_FILE ($FILTERED_COUNT packages)"
echo ""

echo "Step 5: Creating new venv with Python 3.12..."
echo "------------------------------------------------------------------------"
python3.12 -m venv /sphere/.venv
source /sphere/.venv/bin/activate
echo "New venv created with: $(python --version)"
echo ""

echo "Step 6: Upgrading pip..."
echo "------------------------------------------------------------------------"
pip install --upgrade pip
echo ""

echo "Step 7: Installing packages from churro requirements..."
echo "------------------------------------------------------------------------"
echo "This may take several minutes..."
pip install -r "$REQUIREMENTS_FILE"
echo ""

echo "Step 8: Verifying critical packages..."
echo "------------------------------------------------------------------------"
echo "Python version: $(python --version)"
echo "numpy version: $(pip show numpy | grep Version)"
echo "torch version: $(pip show torch | grep Version)"
echo "pandas version: $(pip show pandas | grep Version)"
echo ""

echo "Step 9: Installing featrix-monitor from internal PyPI..."
echo "------------------------------------------------------------------------"
pip install --upgrade --extra-index-url https://bits.featrix.com/pypi/simple --trusted-host bits.featrix.com featrix-monitor || echo "WARNING: featrix-monitor install failed (may be optional)"
echo ""

echo "Step 10: Starting supervisor services..."
echo "------------------------------------------------------------------------"
supervisorctl start all
sleep 3
supervisorctl status
echo ""

echo "========================================================================"
echo "UPGRADE COMPLETE"
echo "========================================================================"
echo ""
echo "Summary:"
echo "  - Python upgraded to 3.12"
echo "  - Old venv backed up to: $BACKUP_DIR"
echo "  - Requirements file: $REQUIREMENTS_FILE"
echo ""
echo "Verify the movie renderer is working:"
echo "  tail -f /var/log/featrix/cluster_movie_renderer.log"
echo ""
echo "If something goes wrong, restore the old venv:"
echo "  supervisorctl stop all"
echo "  rm -rf /sphere/.venv"
echo "  mv $BACKUP_DIR /sphere/.venv"
echo "  supervisorctl start all"
echo ""
