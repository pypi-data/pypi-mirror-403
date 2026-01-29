#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
Download and build geographic foundation data files.

Uses existing Python libraries (uszipcode, pgeocode) to build foundation data
for GeoFoundationEncoder. These libraries handle the data sourcing and caching.

Output files (written to ./data/):
    - zip_locations.parquet: ZIP code centroids with lat/long and metadata (US)
    - fips_locations.parquet: FIPS code (county) centroids with lat/long
    - zip_to_fips.parquet: Crosswalk from ZIP codes to FIPS codes
    - intl_postal.parquet: International postal codes (83 countries)

Dependencies:
    pip install uszipcode pgeocode pandas pyarrow

Usage:
    python download_geographic_data.py [--output-dir ./data]
"""
import argparse
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def build_us_zip_data() -> pd.DataFrame:
    """Build US ZIP code data using uszipcode library.

    uszipcode sources from:
    - US Census Bureau
    - data.census.gov

    Returns DataFrame with columns:
        zip_code, latitude, longitude, city, state, county,
        population, housing_units, land_area_sqmi, water_area_sqmi
    """
    import sqlite3
    import os
    from uszipcode import db

    # Ensure database is downloaded
    db_path = db.DEFAULT_SIMPLE_DB_FILE_PATH
    if not os.path.exists(db_path):
        logger.info("Downloading uszipcode database (first run only)...")
        db.download_db_file(db_path, db.SIMPLE_DB_FILE_DOWNLOAD_URL, 1024*1024, 10*1024*1024)

    logger.info(f"Loading US ZIP data from {db_path}")

    # Read directly from SQLite
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("""
        SELECT
            zipcode as zip_code,
            lat as latitude,
            lng as longitude,
            major_city as city,
            state as state_abbrev,
            county,
            population,
            housing_units,
            land_area_in_sqmi as land_area_sqmi,
            water_area_in_sqmi as water_area_sqmi,
            timezone
        FROM simple_zipcode
        WHERE lat IS NOT NULL AND lng IS NOT NULL
    """, conn)
    conn.close()

    # Ensure 5-digit ZIP codes with leading zeros
    df['zip_code'] = df['zip_code'].astype(str).str.zfill(5)

    logger.info(f"Built US ZIP table: {len(df)} records")
    return df


def build_counties_from_zips(zip_df: pd.DataFrame) -> pd.DataFrame:
    """Build county table from ZIP code data.

    Aggregates ZIP codes by county to compute county centroids.
    Note: uszipcode simple DB doesn't have FIPS codes, so we use county+state as key.
    """
    # Filter to rows with county name
    has_county = zip_df[zip_df['county'].notna()].copy()

    if has_county.empty:
        logger.warning("No county data found in ZIP table")
        return pd.DataFrame()

    # Create a county key (county + state)
    has_county['county_key'] = has_county['county'] + ', ' + has_county['state_abbrev']

    # Group by county
    county_data = []
    for county_key, group in has_county.groupby('county_key'):
        # Compute population-weighted centroid if we have population
        if group['population'].notna().any() and group['population'].sum() > 0:
            weights = group['population'].fillna(0)
            total_weight = weights.sum()
            if total_weight > 0:
                lat = (group['latitude'] * weights).sum() / total_weight
                lng = (group['longitude'] * weights).sum() / total_weight
            else:
                lat = group['latitude'].mean()
                lng = group['longitude'].mean()
        else:
            lat = group['latitude'].mean()
            lng = group['longitude'].mean()

        county_data.append({
            'county_key': county_key,
            'state_abbrev': group['state_abbrev'].iloc[0],
            'county_name': group['county'].iloc[0],
            'latitude': lat,
            'longitude': lng,
            'population': group['population'].sum() if group['population'].notna().any() else None,
            'n_zipcodes': len(group),
        })

    df = pd.DataFrame(county_data)
    logger.info(f"Built county table: {len(df)} county records")
    return df


def build_zip_to_county(zip_df: pd.DataFrame) -> pd.DataFrame:
    """Build ZIP to county crosswalk from ZIP data."""
    has_county = zip_df[zip_df['county'].notna()].copy()

    crosswalk = has_county[['zip_code', 'county', 'state_abbrev']].copy()
    crosswalk = crosswalk.rename(columns={'county': 'county_name'})
    crosswalk['county_key'] = crosswalk['county_name'] + ', ' + crosswalk['state_abbrev']

    logger.info(f"Built ZIP-to-county crosswalk: {len(crosswalk)} mappings")
    return crosswalk


def build_intl_postal_data(countries: list = None) -> pd.DataFrame:
    """Build international postal code data using pgeocode.

    pgeocode sources from:
    - GeoNames database (83 countries)

    Args:
        countries: List of 2-letter country codes. If None, uses major countries.
    """
    import pgeocode

    if countries is None:
        # Major countries with significant postal code systems
        countries = [
            'US', 'CA', 'GB', 'DE', 'FR', 'ES', 'IT', 'NL', 'BE', 'AT', 'CH',
            'AU', 'JP', 'KR', 'IN', 'BR', 'MX', 'PL', 'SE', 'NO', 'DK', 'FI',
        ]

    all_records = []

    for country in countries:
        try:
            logger.info(f"Loading postal codes for {country}...")
            nomi = pgeocode.Nominatim(country)

            # pgeocode stores the data, access it
            if nomi._data is not None and len(nomi._data) > 0:
                df = nomi._data.copy()
                df['country_code'] = country
                all_records.append(df)
                logger.info(f"  {country}: {len(df)} postal codes")
        except Exception as e:
            logger.warning(f"  {country}: Failed to load - {e}")

    if not all_records:
        logger.warning("No international postal codes loaded")
        return pd.DataFrame()

    combined = pd.concat(all_records, ignore_index=True)

    # Standardize column names
    combined = combined.rename(columns={
        'postal_code': 'postal_code',
        'latitude': 'latitude',
        'longitude': 'longitude',
        'place_name': 'place_name',
        'state_name': 'state_name',
        'state_code': 'state_code',
        'county_name': 'county_name',
        'county_code': 'county_code',
    })

    # Keep essential columns
    keep_cols = ['country_code', 'postal_code', 'latitude', 'longitude',
                 'place_name', 'state_name', 'county_name']
    keep_cols = [c for c in keep_cols if c in combined.columns]
    combined = combined[keep_cols]

    logger.info(f"Built international postal table: {len(combined)} records from {len(countries)} countries")
    return combined


def derive_states(county_df: pd.DataFrame) -> pd.DataFrame:
    """Derive state-level data from counties."""
    # State abbreviation to name mapping
    state_names = {
        'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
        'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
        'DC': 'District of Columbia', 'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii',
        'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
        'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine',
        'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota',
        'MS': 'Mississippi', 'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska',
        'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico',
        'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
        'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island',
        'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas',
        'UT': 'Utah', 'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington',
        'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming',
        'AS': 'American Samoa', 'GU': 'Guam', 'MP': 'Northern Mariana Islands',
        'PR': 'Puerto Rico', 'VI': 'Virgin Islands',
    }

    state_data = []
    for state_abbrev, group in county_df.groupby('state_abbrev'):
        name = state_names.get(state_abbrev, state_abbrev)

        # Population-weighted centroid
        if 'population' in group.columns and group['population'].notna().any():
            weights = group['population'].fillna(0)
            total = weights.sum()
            if total > 0:
                lat = (group['latitude'] * weights).sum() / total
                lng = (group['longitude'] * weights).sum() / total
                pop = total
            else:
                lat = group['latitude'].mean()
                lng = group['longitude'].mean()
                pop = None
        else:
            lat = group['latitude'].mean()
            lng = group['longitude'].mean()
            pop = None

        state_data.append({
            'state_abbrev': state_abbrev,
            'state_name': name,
            'latitude': lat,
            'longitude': lng,
            'population': pop,
            'n_counties': len(group),
        })

    df = pd.DataFrame(state_data)
    logger.info(f"Derived {len(df)} state records from counties")
    return df


def main(output_dir: str = './data'):
    """Download all data and build foundation files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Building geographic foundation data in {output_path}")

    # Build US ZIP data
    logger.info("=" * 60)
    logger.info("Step 1: Building US ZIP code data (uszipcode)")
    logger.info("=" * 60)
    zip_df = build_us_zip_data()

    # Build county data from ZIPs
    logger.info("=" * 60)
    logger.info("Step 2: Building county data")
    logger.info("=" * 60)
    county_df = build_counties_from_zips(zip_df)

    # Build ZIP-to-county crosswalk
    zip_to_county = build_zip_to_county(zip_df)

    # Derive states
    states_df = derive_states(county_df)

    # Build international postal codes
    logger.info("=" * 60)
    logger.info("Step 3: Building international postal codes (pgeocode)")
    logger.info("=" * 60)
    intl_df = build_intl_postal_data()

    # Save as parquet
    logger.info("=" * 60)
    logger.info("Step 4: Saving parquet files")
    logger.info("=" * 60)

    zip_file = output_path / 'zip_locations.parquet'
    county_file = output_path / 'county_locations.parquet'
    crosswalk_file = output_path / 'zip_to_county.parquet'
    states_file = output_path / 'state_locations.parquet'
    intl_file = output_path / 'intl_postal.parquet'

    zip_df.to_parquet(zip_file, index=False)
    logger.info(f"Saved {zip_file} ({len(zip_df)} records)")

    if not county_df.empty:
        county_df.to_parquet(county_file, index=False)
        logger.info(f"Saved {county_file} ({len(county_df)} records)")

    if not zip_to_county.empty:
        zip_to_county.to_parquet(crosswalk_file, index=False)
        logger.info(f"Saved {crosswalk_file} ({len(zip_to_county)} records)")

    if not states_df.empty:
        states_df.to_parquet(states_file, index=False)
        logger.info(f"Saved {states_file} ({len(states_df)} records)")

    if not intl_df.empty:
        intl_df.to_parquet(intl_file, index=False)
        logger.info(f"Saved {intl_file} ({len(intl_df)} records)")

    # Summary
    logger.info("=" * 60)
    logger.info("COMPLETE - Foundation data files built:")
    logger.info("=" * 60)
    for f in [zip_file, county_file, crosswalk_file, states_file, intl_file]:
        if f.exists():
            size_mb = f.stat().st_size / (1024 * 1024)
            logger.info(f"  {f.name}: {size_mb:.2f} MB")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download and build geographic foundation data')
    parser.add_argument('--output-dir', default='./data', help='Output directory for parquet files')
    args = parser.parse_args()

    main(args.output_dir)
