#!/bin/bash
#
# install-data.sh - Install foundation data files for Featrix
#
# This script checks for the existence of foundation data files and builds
# any that are missing. Called from node-install to ensure data is available.
#
# Usage:
#   ./install-data.sh [--force] [--with-weather]
#
# Options:
#   --force         Rebuild all data files even if they exist
#   --with-weather  Also download weather data (large, ~150MB per year)
#   --weather-years Start:End year range for weather (default: 2004:current)
#
# Data location: /foundation_data/
#   - geo/zip_locations.parquet
#   - geo/county_locations.parquet
#   - geo/zip_to_county.parquet
#   - geo/state_locations.parquet
#   - geo/intl_postal.parquet
#   - weather/county_weather_YYYY.parquet (if --with-weather)
#   - weather/county_weather_monthly.parquet
#   - weather/county_weather_yearly.parquet
#   - weather/county_weather_normals.parquet
#

set -e

# Configuration
FOUNDATION_DATA_ROOT="${FOUNDATION_DATA_ROOT:-/foundation_data}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORCE_REBUILD=false
WITH_WEATHER=false
WEATHER_START_YEAR=2004
WEATHER_END_YEAR=$(date +%Y)
USE_PREBUILT=true  # Default to downloading pre-built files
PREBUILT_URL="https://bits.featrix.com/foundation-data"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE_REBUILD=true
            shift
            ;;
        --root)
            FOUNDATION_DATA_ROOT="$2"
            shift 2
            ;;
        --with-weather)
            WITH_WEATHER=true
            shift
            ;;
        --weather-years)
            IFS=':' read -r WEATHER_START_YEAR WEATHER_END_YEAR <<< "$2"
            shift 2
            ;;
        --build-from-source)
            USE_PREBUILT=false
            shift
            ;;
        --prebuilt-url)
            PREBUILT_URL="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--force] [--root /path/to/foundation_data] [--with-weather] [--weather-years 2004:2024] [--build-from-source]"
            exit 1
            ;;
    esac
done

echo "========================================"
echo "Featrix Foundation Data Installer"
echo "========================================"
echo "Data root: $FOUNDATION_DATA_ROOT"
echo "Force rebuild: $FORCE_REBUILD"
echo "Use pre-built: $USE_PREBUILT"
echo "With weather: $WITH_WEATHER"
if [[ "$WITH_WEATHER" == "true" ]]; then
    echo "Weather years: $WEATHER_START_YEAR to $WEATHER_END_YEAR"
fi
echo ""

# Function to download a file if it doesn't exist locally
download_if_missing() {
    local filename="$1"
    local subdir="$2"
    local dest_dir="$FOUNDATION_DATA_ROOT/$subdir"
    local dest_file="$dest_dir/$filename"
    local url="$PREBUILT_URL/$filename"

    if [[ -f "$dest_file" ]] && [[ "$FORCE_REBUILD" != "true" ]]; then
        echo "  Already exists: $subdir/$filename"
        return 0
    fi

    echo "  Downloading: $filename ..."
    mkdir -p "$dest_dir"
    if wget -q --show-progress -O "$dest_file" "$url" 2>/dev/null; then
        echo "  Downloaded: $subdir/$filename"
        return 0
    elif curl -fsSL -o "$dest_file" "$url" 2>/dev/null; then
        echo "  Downloaded: $subdir/$filename"
        return 0
    else
        echo "  FAILED: Could not download $filename from $url"
        rm -f "$dest_file"
        return 1
    fi
}

# Create directories
mkdir -p "$FOUNDATION_DATA_ROOT/geo"
if [[ "$WITH_WEATHER" == "true" ]]; then
    mkdir -p "$FOUNDATION_DATA_ROOT/weather"
fi

# Define required files
GEO_FILES=(
    "zip_locations.parquet"
    "county_locations.parquet"
    "zip_to_county.parquet"
    "state_locations.parquet"
    "intl_postal.parquet"
)

# Check which files are missing
missing_geo=false
for file in "${GEO_FILES[@]}"; do
    if [[ ! -f "$FOUNDATION_DATA_ROOT/geo/$file" ]]; then
        echo "Missing: geo/$file"
        missing_geo=true
    else
        echo "Found:   geo/$file"
    fi
done

echo ""

# Build geographic data if needed
if [[ "$missing_geo" == "true" ]] || [[ "$FORCE_REBUILD" == "true" ]]; then
    echo "========================================"
    echo "Installing geographic foundation data..."
    echo "========================================"

    if [[ "$USE_PREBUILT" == "true" ]]; then
        # Download pre-built files from bits.featrix.com
        echo "Downloading pre-built geographic data files..."
        geo_ok=true
        for file in "${GEO_FILES[@]}"; do
            if ! download_if_missing "$file" "geo"; then
                geo_ok=false
            fi
        done

        if [[ "$geo_ok" == "true" ]]; then
            echo ""
            echo "Geographic data downloaded successfully!"
        else
            echo ""
            echo "WARNING: Some geo files failed to download, falling back to build from source..."
            USE_PREBUILT=false
        fi
    fi

    if [[ "$USE_PREBUILT" != "true" ]]; then
        # Build from source using Python scripts
        echo "Building geographic data from source..."

        # Check for required Python packages
        echo "Checking Python dependencies..."
        python3 -c "import uszipcode" 2>/dev/null || {
            echo "Installing uszipcode..."
            pip install uszipcode
        }
        python3 -c "import pgeocode" 2>/dev/null || {
            echo "Installing pgeocode..."
            pip install pgeocode
        }
        python3 -c "import pandas" 2>/dev/null || {
            echo "Installing pandas..."
            pip install pandas
        }
        python3 -c "import pyarrow" 2>/dev/null || {
            echo "Installing pyarrow..."
            pip install pyarrow
        }

        # Run the download script
        echo ""
        echo "Downloading and processing geographic data..."
        python3 "$SCRIPT_DIR/download_geographic_data.py" --output-dir "$FOUNDATION_DATA_ROOT/geo"

        if [[ $? -eq 0 ]]; then
            echo ""
            echo "Geographic data installed successfully!"
        else
            echo ""
            echo "ERROR: Failed to install geographic data"
            exit 1
        fi
    fi
else
    echo "All geographic data files present. Skipping download."
fi

# Build weather data if requested
if [[ "$WITH_WEATHER" == "true" ]]; then
    echo ""
    echo "========================================"
    echo "Weather Data Installation"
    echo "========================================"

    # Check if we have the combined geo_weather.db (preferred) or individual weather files
    weather_files_exist=false
    if [[ -f "$FOUNDATION_DATA_ROOT/geo_weather.db" ]]; then
        weather_files_exist=true
        echo "Found: geo_weather.db (combined geo+weather database)"
    elif [[ -f "$FOUNDATION_DATA_ROOT/weather/county_weather_normals.parquet" ]]; then
        weather_files_exist=true
        echo "Found: weather/county_weather_normals.parquet"
    fi

    if [[ "$weather_files_exist" == "false" ]] || [[ "$FORCE_REBUILD" == "true" ]]; then
        if [[ "$USE_PREBUILT" == "true" ]]; then
            # Try to download pre-built geo_weather.db first (most efficient)
            echo "Downloading pre-built geo_weather.db..."
            if download_if_missing "geo_weather.db" "."; then
                echo ""
                echo "Weather data (geo_weather.db) downloaded successfully!"
            else
                echo "geo_weather.db not available, falling back to individual files..."
                # Fall back to downloading individual weather parquet files
                WEATHER_AGG_FILES=(
                    "county_weather_monthly.parquet"
                    "county_weather_yearly.parquet"
                    "county_weather_normals.parquet"
                )
                weather_ok=true
                for file in "${WEATHER_AGG_FILES[@]}"; do
                    if ! download_if_missing "$file" "weather"; then
                        weather_ok=false
                    fi
                done

                # Download yearly files
                for year in $(seq $WEATHER_START_YEAR $WEATHER_END_YEAR); do
                    if ! download_if_missing "county_weather_${year}.parquet" "weather"; then
                        echo "  (Year $year not available, continuing...)"
                    fi
                done

                if [[ "$weather_ok" == "true" ]]; then
                    echo ""
                    echo "Weather data downloaded successfully!"
                else
                    echo ""
                    echo "WARNING: Some weather files failed, falling back to build from source..."
                    USE_PREBUILT=false
                fi
            fi
        fi

        if [[ "$USE_PREBUILT" != "true" ]]; then
            echo "Building weather data from source..."
            echo "Years: $WEATHER_START_YEAR to $WEATHER_END_YEAR"
            echo ""

            # Check for required Python packages
            python3 -c "import requests" 2>/dev/null || {
                echo "Installing requests..."
                pip install requests
            }
            python3 -c "import tqdm" 2>/dev/null || {
                echo "Installing tqdm..."
                pip install tqdm
            }

            # Run the weather download script
            python3 "$SCRIPT_DIR/download_weather_data.py" \
                --output-dir "$FOUNDATION_DATA_ROOT/weather" \
                --start-year "$WEATHER_START_YEAR" \
                --end-year "$WEATHER_END_YEAR"

            if [[ $? -eq 0 ]]; then
                echo ""
                echo "Weather data installed successfully!"
            else
                echo ""
                echo "WARNING: Failed to install weather data (non-fatal)"
            fi
        fi
    else
        echo "Weather data already present. Skipping download."
        echo "(Use --force to rebuild)"
    fi
fi

# Verify installation
echo ""
echo "========================================"
echo "Verifying installation..."
echo "========================================"

all_ok=true
for file in "${GEO_FILES[@]}"; do
    if [[ -f "$FOUNDATION_DATA_ROOT/geo/$file" ]]; then
        size=$(du -h "$FOUNDATION_DATA_ROOT/geo/$file" | cut -f1)
        echo "OK: geo/$file ($size)"
    else
        echo "MISSING: geo/$file"
        all_ok=false
    fi
done

# Verify weather files if requested
if [[ "$WITH_WEATHER" == "true" ]]; then
    echo ""
    echo "Weather data:"
    weather_ok=true

    # Check for aggregate files
    WEATHER_AGG_FILES=(
        "county_weather_monthly.parquet"
        "county_weather_yearly.parquet"
        "county_weather_normals.parquet"
    )
    for file in "${WEATHER_AGG_FILES[@]}"; do
        if [[ -f "$FOUNDATION_DATA_ROOT/weather/$file" ]]; then
            size=$(du -h "$FOUNDATION_DATA_ROOT/weather/$file" | cut -f1)
            echo "OK: weather/$file ($size)"
        else
            echo "MISSING: weather/$file"
            weather_ok=false
        fi
    done

    # Count yearly files
    yearly_count=$(ls -1 "$FOUNDATION_DATA_ROOT/weather/county_weather_"[0-9]*.parquet 2>/dev/null | wc -l | tr -d ' ')
    expected_years=$((WEATHER_END_YEAR - WEATHER_START_YEAR + 1))
    echo "Yearly files: $yearly_count (expected: $expected_years)"

    if [[ "$weather_ok" == "false" ]]; then
        echo "WARNING: Some weather files are missing"
    fi
fi

echo ""
if [[ "$all_ok" == "true" ]]; then
    echo "========================================"
    echo "Foundation data installation complete!"
    echo "========================================"
    echo ""
    echo "Data location: $FOUNDATION_DATA_ROOT"
    echo ""
    echo "To use in Python:"
    echo "  from featrix.neural.geo_foundation import get_geo_data_manager"
    echo "  dm = get_geo_data_manager()"
    echo "  dm.set_data_dir('$FOUNDATION_DATA_ROOT/geo')"
    echo ""
    exit 0
else
    echo "========================================"
    echo "ERROR: Some files are missing!"
    echo "========================================"
    exit 1
fi
