#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
Build SQLite database of geographic + weather data for training Featrix ES.

Creates a SQLite database with one row per (FIPS, date) containing:
- fips: 5-digit county FIPS code
- date: Date (YYYY-MM-DD)
- latitude: County centroid latitude
- longitude: County centroid longitude
- state: State abbreviation
- county_name: County name
- zip_code: Representative ZIP code for the county
- tmax: Maximum temperature (°C)
- tmin: Minimum temperature (°C)
- tavg: Average temperature (°C)
- prcp: Precipitation (mm)
- tmax_normal: 30-year normal max temp for this month
- tmin_normal: 30-year normal min temp for this month
- tavg_normal: 30-year normal avg temp for this month
- prcp_normal: 30-year normal daily precip for this month
- day_of_year: 1-366
- month: 1-12
- day_of_week: 0-6 (Monday=0)

Output:
    geo_weather.db - SQLite database (~2-3GB for 25 years of data)

Usage:
    python build_geo_weather_db.py --start-year 2000 --end-year 2024 --output geo_weather.db
"""
import argparse
import logging
import sqlite3
from datetime import date
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# State name to abbreviation mapping
STATE_NAME_TO_ABBREV = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
    'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
    'District of Columbia': 'DC', 'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI',
    'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
    'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME',
    'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN',
    'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE',
    'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM',
    'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH',
    'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI',
    'South Carolina': 'SC', 'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX',
    'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA',
    'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY',
    'Puerto Rico': 'PR', 'Virgin Islands': 'VI', 'Guam': 'GU',
    'American Samoa': 'AS', 'Northern Mariana Islands': 'MP',
}


def create_database(db_path: Path) -> sqlite3.Connection:
    """Create SQLite database with schema."""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS geo_weather (
            fips TEXT NOT NULL,
            date TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            state TEXT,
            county_name TEXT,
            zip_code TEXT,
            tmax REAL,
            tmin REAL,
            tavg REAL,
            prcp REAL,
            tmax_normal REAL,
            tmin_normal REAL,
            tavg_normal REAL,
            prcp_normal REAL,
            day_of_year INTEGER,
            month INTEGER,
            day_of_week INTEGER,
            PRIMARY KEY (fips, date)
        )
    ''')

    # Create indexes for common queries
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_fips ON geo_weather(fips)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON geo_weather(date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_state ON geo_weather(state)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_county ON geo_weather(county_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_zip ON geo_weather(zip_code)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_month ON geo_weather(month)')

    conn.commit()
    return conn


def load_weather_year(weather_dir: Path, year: int) -> Optional[pd.DataFrame]:
    """Load weather data for a year."""
    year_file = weather_dir / f'county_weather_{year}.parquet'
    if not year_file.exists():
        return None

    df = pd.read_parquet(year_file)
    df['date'] = pd.to_datetime(df['date'])
    df['fips'] = df['fips'].astype(str).str.zfill(5)

    # Convert weather columns to float
    for col in ['tmax', 'tmin', 'tavg', 'prcp']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


def load_climate_normals(weather_dir: Path) -> Dict[Tuple[str, int], Tuple[float, float, float, float]]:
    """Load climate normals as a lookup dict: (fips, month) -> (tmax, tmin, tavg, prcp)."""
    normals_file = weather_dir / 'county_weather_normals.parquet'
    if not normals_file.exists():
        logger.warning("Climate normals not found")
        return {}

    df = pd.read_parquet(normals_file)
    df['fips'] = df['fips'].astype(str).str.zfill(5)

    normals = {}
    for _, row in df.iterrows():
        key = (row['fips'], int(row['month']))
        normals[key] = (
            float(row.get('tmax_normal', 0) or 0),
            float(row.get('tmin_normal', 0) or 0),
            float(row.get('tavg_normal', 0) or 0),
            float(row.get('prcp_daily_normal', 0) or 0),
        )

    logger.info(f"Loaded {len(normals)} climate normals")
    return normals


def load_county_to_zip(geo_dir: Path) -> Dict[str, str]:
    """Load county -> representative ZIP code mapping.

    Uses zip_to_county crosswalk to find a ZIP for each county.
    Returns first ZIP found for each (county_name, state) combination.
    """
    crosswalk_file = geo_dir / 'zip_to_county.parquet'
    if not crosswalk_file.exists():
        logger.warning("ZIP-to-county crosswalk not found")
        return {}

    df = pd.read_parquet(crosswalk_file)

    # Build (county_name, state) -> first ZIP code
    # We'll normalize county names for matching
    county_to_zip = {}
    for _, row in df.iterrows():
        county_name = str(row.get('county_name', '')).strip()
        state = str(row.get('state_abbrev', '')).strip()
        zip_code = str(row.get('zip_code', '')).strip().zfill(5)

        if county_name and state and zip_code:
            # Store with various key formats for flexible matching
            key = f"{county_name}, {state}"
            if key not in county_to_zip:
                county_to_zip[key] = zip_code

    logger.info(f"Loaded {len(county_to_zip)} county->ZIP mappings")
    return county_to_zip


def load_fips_coordinates(weather_dir: Path, geo_dir: Path) -> Dict[str, Tuple[float, float, str, str, str]]:
    """Load FIPS -> (lat, long, state, county_name, zip_code) mapping.

    Uses Census county gazetteer if available, otherwise approximates from state centroids.
    Also loads ZIP codes from the crosswalk file.
    """
    # Load county-to-ZIP mapping
    county_to_zip = load_county_to_zip(geo_dir)

    # Try to load Census gazetteer (has FIPS + coordinates)
    gazetteer_file = geo_dir / 'county_gazetteer.parquet'
    if gazetteer_file.exists():
        df = pd.read_parquet(gazetteer_file)
        result = {}
        for _, row in df.iterrows():
            fips = str(row['GEOID']).zfill(5) if 'GEOID' in row else str(row['fips']).zfill(5)
            lat = row.get('INTPTLAT', row.get('latitude', 0))
            long = row.get('INTPTLONG', row.get('longitude', 0))
            state = row.get('USPS', row.get('state', ''))
            county_name = row.get('NAME', row.get('county_name', ''))
            # Look up ZIP code
            zip_key = f"{county_name}, {state}"
            zip_code = county_to_zip.get(zip_key, '')
            result[fips] = (float(lat), float(long), state, county_name, zip_code)
        logger.info(f"Loaded {len(result)} FIPS coordinates from gazetteer")
        return result

    # Fall back to extracting from weather data + state centroids
    logger.info("Gazetteer not found, extracting county info from weather data")

    # Get FIPS -> (state, county_name, region_name) from weather data
    fips_info = {}
    for year in range(2024, 1999, -1):
        df = load_weather_year(weather_dir, year)
        if df is not None:
            for _, row in df.drop_duplicates('fips').iterrows():
                fips = row['fips']
                state_name = row.get('state_name', '')
                state_abbrev = STATE_NAME_TO_ABBREV.get(state_name, '')
                region_name = row.get('region_name', '')

                # Extract county name from region_name (format: "AL: Autauga" or "AL: Baldwin County")
                county_name = ''
                if region_name and ':' in region_name:
                    county_name = region_name.split(':', 1)[1].strip()
                    # Remove " County" suffix if present for cleaner names
                    if county_name.endswith(' County'):
                        county_name = county_name[:-7]

                if fips not in fips_info and state_abbrev:
                    fips_info[fips] = (state_abbrev, county_name)
            break

    # Load state centroids
    state_coords = {}
    state_file = geo_dir / 'state_locations.parquet'
    if state_file.exists():
        states_df = pd.read_parquet(state_file)
        for _, row in states_df.iterrows():
            state_coords[row['state_abbrev']] = (row['latitude'], row['longitude'])

    # Build FIPS -> (lat, long, state, county_name, zip_code)
    result = {}
    for fips, (state, county_name) in fips_info.items():
        if state in state_coords:
            lat, long = state_coords[state]
        else:
            # Default to US center
            lat, long = 39.8, -98.5

        # Look up ZIP code - try with and without " County" suffix
        zip_code = ''
        for county_variant in [county_name, f"{county_name} County"]:
            zip_key = f"{county_variant}, {state}"
            if zip_key in county_to_zip:
                zip_code = county_to_zip[zip_key]
                break

        result[fips] = (lat, long, state, county_name, zip_code)

    logger.info(f"Built {len(result)} FIPS coordinates from weather data")
    return result


def insert_year(
    conn: sqlite3.Connection,
    year: int,
    weather_dir: Path,
    fips_coords: Dict[str, Tuple[float, float, str, str, str]],
    normals: Dict[Tuple[str, int], Tuple[float, float, float, float]],
    batch_size: int = 10000,
):
    """Insert all records for a year into the database."""
    df = load_weather_year(weather_dir, year)
    if df is None:
        logger.warning(f"No weather data for {year}")
        return 0

    cursor = conn.cursor()
    records = []
    inserted = 0

    for _, row in tqdm(df.iterrows(), total=len(df), desc=f"Processing {year}"):
        fips = row['fips']
        dt = row['date']

        # Skip rows with invalid dates
        if pd.isna(dt):
            continue

        date_str = dt.strftime('%Y-%m-%d')
        month = dt.month

        # Get coordinates, county_name, zip_code
        coord_info = fips_coords.get(fips, (None, None, None, None, None))
        lat, long, state, county_name, zip_code = coord_info

        # Get weather
        tmax = row['tmax'] if pd.notna(row['tmax']) else None
        tmin = row['tmin'] if pd.notna(row['tmin']) else None
        tavg = row['tavg'] if pd.notna(row['tavg']) else None
        prcp = row['prcp'] if pd.notna(row['prcp']) else None

        # Get normals
        normal = normals.get((fips, month), (None, None, None, None))
        tmax_normal, tmin_normal, tavg_normal, prcp_normal = normal

        # Temporal features
        day_of_year = dt.timetuple().tm_yday
        day_of_week = dt.weekday()

        records.append((
            fips, date_str, lat, long, state, county_name, zip_code,
            tmax, tmin, tavg, prcp,
            tmax_normal, tmin_normal, tavg_normal, prcp_normal,
            day_of_year, month, day_of_week,
        ))

        if len(records) >= batch_size:
            cursor.executemany('''
                INSERT OR REPLACE INTO geo_weather
                (fips, date, latitude, longitude, state, county_name, zip_code,
                 tmax, tmin, tavg, prcp,
                 tmax_normal, tmin_normal, tavg_normal, prcp_normal,
                 day_of_year, month, day_of_week)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', records)
            inserted += len(records)
            records = []

    # Insert remaining
    if records:
        cursor.executemany('''
            INSERT OR REPLACE INTO geo_weather
            (fips, date, latitude, longitude, state, county_name, zip_code,
             tmax, tmin, tavg, prcp,
             tmax_normal, tmin_normal, tavg_normal, prcp_normal,
             day_of_year, month, day_of_week)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', records)
        inserted += len(records)

    conn.commit()
    return inserted


def main(
    weather_dir: str = '/foundation_data/weather',
    geo_dir: str = '/foundation_data/geo',
    output_file: str = 'geo_weather.db',
    start_year: int = 2000,
    end_year: int = 2024,
):
    """Build SQLite database of geo+weather data."""
    weather_path = Path(weather_dir)
    geo_path = Path(geo_dir)
    output_path = Path(output_file)

    logger.info("=" * 60)
    logger.info("Building Geo+Weather SQLite Database")
    logger.info("=" * 60)
    logger.info(f"Weather data: {weather_path}")
    logger.info(f"Geo data: {geo_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Years: {start_year} to {end_year}")
    logger.info("")

    # Create database
    if output_path.exists():
        logger.info(f"Removing existing database: {output_path}")
        output_path.unlink()

    conn = create_database(output_path)

    # Load reference data
    normals = load_climate_normals(weather_path)
    fips_coords = load_fips_coordinates(weather_path, geo_path)

    # Process each year
    total_records = 0
    for year in range(start_year, end_year + 1):
        count = insert_year(conn, year, weather_path, fips_coords, normals)
        total_records += count
        logger.info(f"{year}: Inserted {count:,} records")

    conn.close()

    # Summary
    size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info("")
    logger.info("=" * 60)
    logger.info("COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total records: {total_records:,}")
    logger.info(f"Database size: {size_mb:.1f} MB")
    logger.info(f"Output: {output_path}")


def export_to_parquet(db_path: str, output_path: str, sample_frac: float = None):
    """Export SQLite database to parquet for Featrix training.

    Args:
        db_path: Path to SQLite database
        output_path: Path for output parquet file
        sample_frac: Optional fraction to sample (e.g., 0.1 for 10%)
    """
    import sqlite3

    conn = sqlite3.connect(db_path)

    query = "SELECT * FROM geo_weather"
    if sample_frac:
        # SQLite doesn't have TABLESAMPLE, use random ordering with limit
        count_query = "SELECT COUNT(*) FROM geo_weather"
        total = pd.read_sql_query(count_query, conn).iloc[0, 0]
        limit = int(total * sample_frac)
        query = f"SELECT * FROM geo_weather ORDER BY RANDOM() LIMIT {limit}"

    logger.info(f"Exporting to {output_path}...")
    df = pd.read_sql_query(query, conn)
    conn.close()

    df.to_parquet(output_path, index=False)
    size_mb = Path(output_path).stat().st_size / (1024 * 1024)
    logger.info(f"Exported {len(df):,} records ({size_mb:.1f} MB)")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build geo+weather SQLite database')
    parser.add_argument('--weather-dir', default='/foundation_data/weather', help='Weather data directory')
    parser.add_argument('--geo-dir', default='/foundation_data/geo', help='Geographic data directory')
    parser.add_argument('--output', default='geo_weather.db', help='Output SQLite file')
    parser.add_argument('--start-year', type=int, default=2000, help='Start year')
    parser.add_argument('--end-year', type=int, default=2024, help='End year')
    parser.add_argument('--export-parquet', help='Also export to parquet file')
    parser.add_argument('--sample', type=float, help='Sample fraction for export (e.g., 0.1)')
    args = parser.parse_args()

    main(args.weather_dir, args.geo_dir, args.output, args.start_year, args.end_year)

    if args.export_parquet:
        export_to_parquet(args.output, args.export_parquet, args.sample)
