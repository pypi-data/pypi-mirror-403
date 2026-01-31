#!/bin/bash

check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "$1 is not installed. Installing..."
        pip install "$1"
        exit 1
    fi
}

check_directory() {
    if [ ! -d "$1" ]; then
        echo "Directory '$1' not found."
        exit 1
    fi
}

check_file() {
    if [ ! -f "$1" ]; then
        echo "File '$1' not found."
        exit 1
    fi
}

# ✅ Check required tools
check_command flit
check_command flake8

# ✅ Check required project files
check_file pyproject.toml
check_file README.md
check_file LICENSE

# ✅ Clean previous builds
rm -rf dist build *.egg-info
find . -name "*.pyc" -exec rm -f {} \;

# ✅ Run code style checks
flake8 .

# ✅ Build and upload using flit
flit publish

# ✅ Cleanup (optional)
rm -rf dist build *.egg-info
