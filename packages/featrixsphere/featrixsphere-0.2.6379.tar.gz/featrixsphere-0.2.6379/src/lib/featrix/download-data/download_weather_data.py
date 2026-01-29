#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
Download NOAA nClimGrid-Daily EpiNOAA county-level weather data.

Downloads daily temperature and precipitation data aggregated to US counties
from 1951-present. Data is sourced from NOAA's nClimGrid-Daily EpiNOAA
analysis-ready dataset on AWS S3.

Data source:
    https://noaa-nclimgrid-daily-pds.s3.amazonaws.com/EpiNOAA/v1-0-0/parquet/cty/

Variables:
    - tmax: Daily maximum temperature (°C)
    - tmin: Daily minimum temperature (°C)
    - tavg: Daily average temperature (°C)
    - prcp: Daily precipitation (mm)

Output files (written to ./data/weather/):
    - county_weather_YYYY.parquet: Daily weather by FIPS code for each year
    - county_weather_monthly.parquet: Monthly aggregates by FIPS (all years)
    - county_weather_yearly.parquet: Yearly aggregates by FIPS (all years)
    - county_weather_normals.parquet: 30-year climate normals by FIPS

Dependencies:
    pip install pandas pyarrow requests tqdm

Usage:
    python download_weather_data.py [--output-dir ./data/weather] [--start-year 2004] [--end-year 2024]
"""
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# AWS S3 bucket for nClimGrid-Daily EpiNOAA data
# Structure: EpiNOAA/v1-0-0/parquet/cty/YEAR={year}/STATUS=scaled/{YYYYMM}.parquet
EPINOAA_BASE_URL = "https://noaa-nclimgrid-daily-pds.s3.amazonaws.com/EpiNOAA/v1-0-0/parquet/cty"


def download_month(year: int, month: int) -> Optional[pd.DataFrame]:
    """Download weather data for a single month.

    Args:
        year: Year (1951-present)
        month: Month (1-12)

    Returns:
        DataFrame with columns: fips, date, tmax, tmin, tavg, prcp, state_name, region_name
        Or None if download fails
    """
    month_str = f"{year}{month:02d}"
    url = f"{EPINOAA_BASE_URL}/YEAR={year}/STATUS=scaled/{month_str}.parquet"

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        # Read parquet directly from bytes
        import io
        df = pd.read_parquet(io.BytesIO(response.content))

        # Convert temperature/precip columns to numeric (they come as strings sometimes)
        for col in ['tmax', 'tmin', 'tavg', 'prcp']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return None  # Month not available yet
        logger.warning(f"HTTP error for {month_str}: {e.response.status_code}")
        return None
    except Exception as e:
        logger.warning(f"Error downloading {month_str}: {e}")
        return None


def download_year(year: int, parallel: bool = True) -> Optional[pd.DataFrame]:
    """Download all months for a year.

    Args:
        year: Year to download
        parallel: Use parallel downloads for months

    Returns:
        DataFrame with all months combined
    """
    months_data = []

    if parallel:
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(download_month, year, m): m for m in range(1, 13)}
            for future in as_completed(futures):
                month = futures[future]
                try:
                    df = future.result()
                    if df is not None:
                        months_data.append(df)
                except Exception as e:
                    logger.warning(f"Error processing {year}-{month:02d}: {e}")
    else:
        for month in range(1, 13):
            df = download_month(year, month)
            if df is not None:
                months_data.append(df)

    if not months_data:
        return None

    combined = pd.concat(months_data, ignore_index=True)
    return combined


def download_weather_range(
    start_year: int,
    end_year: int,
    output_dir: Path,
) -> List[Path]:
    """Download weather data for a range of years.

    Args:
        start_year: First year to download
        end_year: Last year to download (inclusive)
        output_dir: Directory to save yearly files

    Returns:
        List of paths to saved parquet files
    """
    saved_files = []

    for year in tqdm(range(start_year, end_year + 1), desc="Downloading years"):
        year_file = output_dir / f"county_weather_{year}.parquet"

        # Skip if already downloaded
        if year_file.exists():
            logger.info(f"  {year}: Already exists, skipping")
            saved_files.append(year_file)
            continue

        df = download_year(year)

        if df is not None:
            # Normalize FIPS codes
            df['fips'] = df['fips'].astype(str).str.zfill(5)

            # Keep only essential columns
            keep_cols = ['fips', 'date', 'tmax', 'tmin', 'tavg', 'prcp', 'state_name', 'region_name']
            keep_cols = [c for c in keep_cols if c in df.columns]
            df = df[keep_cols]

            # Save
            df.to_parquet(year_file, index=False)
            saved_files.append(year_file)
            logger.info(f"  {year}: {len(df)} records saved")
        else:
            logger.warning(f"  {year}: No data available")

    return saved_files


def compute_monthly_aggregates(yearly_files: List[Path], output_file: Path) -> pd.DataFrame:
    """Compute monthly aggregates from yearly files.

    Args:
        yearly_files: List of yearly parquet files
        output_file: Path to save monthly aggregates

    Returns:
        DataFrame with monthly aggregates
    """
    all_monthly = []

    for year_file in tqdm(yearly_files, desc="Computing monthly aggregates"):
        df = pd.read_parquet(year_file)

        # Ensure date is datetime
        df['date'] = pd.to_datetime(df['date'])
        df['year_month'] = df['date'].dt.to_period('M')

        # Aggregate by fips and month
        monthly = df.groupby(['fips', 'year_month']).agg({
            'tmax': ['mean', 'max'],
            'tmin': ['mean', 'min'],
            'tavg': 'mean',
            'prcp': ['sum', 'mean', 'max'],
        })

        # Flatten column names
        monthly.columns = ['_'.join(col).strip() for col in monthly.columns.values]
        monthly = monthly.reset_index()

        # Convert period to date
        monthly['year'] = monthly['year_month'].dt.year
        monthly['month'] = monthly['year_month'].dt.month
        monthly = monthly.drop(columns=['year_month'])

        all_monthly.append(monthly)

    if not all_monthly:
        return pd.DataFrame()

    combined = pd.concat(all_monthly, ignore_index=True)
    combined.to_parquet(output_file, index=False)
    logger.info(f"Saved monthly aggregates: {len(combined)} records")

    return combined


def compute_yearly_aggregates(yearly_files: List[Path], output_file: Path) -> pd.DataFrame:
    """Compute yearly aggregates from yearly files.

    Args:
        yearly_files: List of yearly parquet files
        output_file: Path to save yearly aggregates

    Returns:
        DataFrame with yearly aggregates
    """
    all_yearly = []

    for year_file in tqdm(yearly_files, desc="Computing yearly aggregates"):
        df = pd.read_parquet(year_file)

        # Ensure date is datetime
        df['date'] = pd.to_datetime(df['date'])
        year = df['date'].dt.year.iloc[0]

        # Aggregate by fips
        yearly = df.groupby('fips').agg({
            'tmax': ['mean', 'max'],
            'tmin': ['mean', 'min'],
            'tavg': 'mean',
            'prcp': ['sum', 'mean', 'max'],
        })

        # Flatten column names
        yearly.columns = ['_'.join(col).strip() for col in yearly.columns.values]
        yearly = yearly.reset_index()
        yearly['year'] = year

        all_yearly.append(yearly)

    if not all_yearly:
        return pd.DataFrame()

    combined = pd.concat(all_yearly, ignore_index=True)
    combined.to_parquet(output_file, index=False)
    logger.info(f"Saved yearly aggregates: {len(combined)} records")

    return combined


def compute_climate_normals(yearly_files: List[Path], output_file: Path, years: int = 30) -> pd.DataFrame:
    """Compute climate normals (30-year averages) from yearly files.

    Args:
        yearly_files: List of yearly parquet files
        output_file: Path to save climate normals
        years: Number of years for normal period (default: 30)

    Returns:
        DataFrame with climate normals by FIPS and month
    """
    # Use last N years
    recent_files = sorted(yearly_files)[-years:]

    if len(recent_files) < 10:
        logger.warning(f"Only {len(recent_files)} years available, normals may be less reliable")

    all_data = []
    for year_file in tqdm(recent_files, desc="Computing climate normals"):
        df = pd.read_parquet(year_file)
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.month
        all_data.append(df)

    combined = pd.concat(all_data, ignore_index=True)

    # Compute normals by fips and month
    normals = combined.groupby(['fips', 'month']).agg({
        'tmax': 'mean',
        'tmin': 'mean',
        'tavg': 'mean',
        'prcp': ['mean', 'sum'],  # mean daily, total monthly avg
    })

    # Flatten column names
    normals.columns = ['_'.join(col).strip() if col[1] else col[0] for col in normals.columns.values]
    normals = normals.reset_index()

    # Rename for clarity
    normals = normals.rename(columns={
        'tmax_mean': 'tmax_normal',
        'tmin_mean': 'tmin_normal',
        'tavg_mean': 'tavg_normal',
        'prcp_mean': 'prcp_daily_normal',
        'prcp_sum': 'prcp_monthly_total_normal',
    })

    # Add metadata
    year_range = f"{recent_files[0].stem.split('_')[-1]}-{recent_files[-1].stem.split('_')[-1]}"
    normals['normal_period'] = year_range

    normals.to_parquet(output_file, index=False)
    logger.info(f"Saved climate normals: {len(normals)} records ({year_range})")

    return normals


def main(
    output_dir: str = './data/weather',
    start_year: int = 2004,
    end_year: int = None,
    skip_aggregates: bool = False,
):
    """Download weather data and build foundation files."""
    if end_year is None:
        end_year = datetime.now().year  # Include current year

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("NOAA nClimGrid-Daily County Weather Data Download")
    logger.info("=" * 60)
    logger.info(f"Years: {start_year} to {end_year} ({end_year - start_year + 1} years)")
    logger.info(f"Output: {output_path}")
    logger.info("")

    # Download yearly data
    logger.info("Step 1: Downloading daily weather data by year")
    logger.info("-" * 60)

    yearly_files = download_weather_range(start_year, end_year, output_path)

    if not yearly_files:
        logger.error("No data downloaded!")
        return

    logger.info(f"Downloaded {len(yearly_files)} years of data")

    if skip_aggregates:
        logger.info("Skipping aggregate computation (--skip-aggregates)")
    else:
        # Compute monthly aggregates
        logger.info("")
        logger.info("Step 2: Computing monthly aggregates")
        logger.info("-" * 60)
        monthly_file = output_path / 'county_weather_monthly.parquet'
        compute_monthly_aggregates(yearly_files, monthly_file)

        # Compute yearly aggregates
        logger.info("")
        logger.info("Step 3: Computing yearly aggregates")
        logger.info("-" * 60)
        yearly_agg_file = output_path / 'county_weather_yearly.parquet'
        compute_yearly_aggregates(yearly_files, yearly_agg_file)

        # Compute climate normals
        logger.info("")
        logger.info("Step 4: Computing climate normals (30-year averages)")
        logger.info("-" * 60)
        normals_file = output_path / 'county_weather_normals.parquet'
        compute_climate_normals(yearly_files, normals_file)

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("COMPLETE - Weather data files:")
    logger.info("=" * 60)

    total_size = 0
    for f in sorted(output_path.glob('*.parquet')):
        size_mb = f.stat().st_size / (1024 * 1024)
        total_size += size_mb
        logger.info(f"  {f.name}: {size_mb:.2f} MB")

    logger.info(f"  TOTAL: {total_size:.2f} MB")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download NOAA county weather data')
    parser.add_argument('--output-dir', default='./data/weather', help='Output directory')
    parser.add_argument('--start-year', type=int, default=2004, help='Start year (default: 2004)')
    parser.add_argument('--end-year', type=int, default=None, help='End year (default: current year)')
    parser.add_argument('--skip-aggregates', action='store_true', help='Skip computing aggregates')
    args = parser.parse_args()

    main(args.output_dir, args.start_year, args.end_year, args.skip_aggregates)
