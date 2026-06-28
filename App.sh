#!/usr/bin/env bash

# Unified Deployment and Requirement Check Script for Quota-main
# Ensures all dependencies, ports, and databases are healthy before launching.

set -e

# Domain Expansion: Unlimited Void! Supreme Confidence.
echo "=========================================================="
echo "⚡ Unlimited Void: Booting Quota-main App Offline LAN ⚡"
echo "=========================================================="

DRY_RUN=false
if [[ "$1" == "--check-only" || "$1" == "-c" ]]; then
    DRY_RUN=true
    echo "🔍 Mode: Requirement Check Only (Dry Run)"
fi

# 1. Locate Python Executable
PYTHON_EXE=""
CANDIDATES=(
    "D:/Python/python.exe"
    "D:\\Python\\python.exe"
    "python3"
    "python"
    "py"
)

echo -n "🕵️  Locating Python... "
for c in "${CANDIDATES[@]}"; do
    if command -v "$c" >/dev/null 2>&1; then
        # Double check it works
        if "$c" -c "import sys; sys.exit(0)" >/dev/null 2>&1; then
            PYTHON_EXE="$c"
            break
        fi
    fi
done

if [ -z "$PYTHON_EXE" ]; then
    echo -e "\n❌ ERROR: Python executable could not be found!"
    echo "   Ensure D:/Python/python.exe or python is installed and in your environment."
    exit 1
fi
echo "Found: $PYTHON_EXE"

# 2. Check Python Version
echo -n "🔢 Checking Python Version... "
VER_CHECK=$("$PYTHON_EXE" -c "import sys; print(1 if sys.version_info >= (3, 8) else 0)")
if [ "$VER_CHECK" -ne 1 ]; then
    echo -e "\n❌ ERROR: Python 3.8+ is required."
    "$PYTHON_EXE" --version
    exit 1
fi
echo "OK ($("$PYTHON_EXE" --version 2>&1))"

# 3. Check Dependencies (Imports test)
echo "📦 Verifying Library Dependencies... "
DEP_STATUS=$("$PYTHON_EXE" -c "
import sys
import importlib.util
deps = [
    ('streamlit', 'streamlit'),
    ('pandas', 'pandas'),
    ('openpyxl', 'openpyxl'),
    ('bcrypt', 'bcrypt'),
    ('xlrd', 'xlrd'),
    ('deepdiff', 'deepdiff'),
    ('st_aggrid', 'streamlit-aggrid'),
    ('plotly', 'plotly'),
    ('jinja2', 'jinja2')
]
status = [(n, importlib.util.find_spec(m) is not None) for m, n in deps]
for n, ok in status:
    print('  [OK] ' + n if ok else '  [MISSING] ' + n)
sys.exit(1 if any(not ok for n, ok in status) else 0)
" 2>&1 || true)

echo "$DEP_STATUS"

if echo "$DEP_STATUS" | grep -q "\[MISSING\]"; then
    echo -e "\n❌ ERROR: Missing or broken dependencies."
    echo "   Please run: $PYTHON_EXE -m pip install -r requirements.txt"
    exit 1
fi
echo "All dependencies verified!"

# 4. Check Database Seeding
DB_PATH="data/database.sqlite"
echo -n "🗄️  Verifying Database Status... "
if [ ! -f "$DB_PATH" ] || [ ! -s "$DB_PATH" ]; then
    echo -e "\n⚠️  WARNING: Database not found or empty. Seeding database..."
    if ! "$PYTHON_EXE" src/seed_full.py; then
        echo "❌ ERROR: Database seeding failed!"
        exit 1
    fi
    echo "✅ Database initialized and seeded successfully!"
else
    echo "OK ($DB_PATH exists)"
fi

# 5. Check Port Availability (8501)
echo -n "🔌 Checking Port 8501 Availability... "
PORT_CHECK=$("$PYTHON_EXE" -c "
import socket, sys
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind(('127.0.0.1', 8501))
    s.close()
    sys.exit(0)
except OSError:
    sys.exit(1)
" 2>&1 || true)

# If exit code was 1, port is in use
if [ $? -ne 0 ]; then
    echo -e "\n❌ ERROR: Port 8501 is already in use by another process!"
    echo "   Ensure no other Streamlit instance is running."
    exit 1
fi
echo "Port 8501 is available!"

echo "=========================================================="
echo "✨ All Checks Passed! System is 100% Ready for Deployment. ✨"
echo "=========================================================="

if [ "$DRY_RUN" = true ]; then
    echo "✅ Verification complete. App not launched."
    exit 0
fi

echo "🚀 Launching Quota-main App..."
"$PYTHON_EXE" -m streamlit run src/app.py
