#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
Download road, interstate, truck stop, and rest area data.

This module provides functions to download and process transportation infrastructure
data from various public sources.

=============================================================================
DATA SOURCES
=============================================================================

## Government Data Sources

### Interstate Highways
- Data.gov: https://catalog.data.gov/dataset?q=Interstate+Highways
  - 285+ datasets, CSV/Shapefile/GeoJSON/KML formats

- Bureau of Transportation Statistics (NTAD):
  https://www.bts.gov/geography/geospatial-portal/NTAD-direct-download
  - National Transportation Atlas Database
  - ARNOLD (All Roads Network Of Linear Referenced Data)

- FHWA HPMS: https://www.fhwa.dot.gov/policyinformation/hpms/shapefiles.cfm
  - Highway Performance Monitoring System shapefiles

- USGS National Transportation Dataset:
  https://data.usgs.gov/datacatalog/data/USGS:ad3d631d-f51f-4b6a-91a3-e617d6a58b4e
  - Roads, railroads, trails, airports (Shapefile/Geodatabase)

- Census TIGER/Line:
  https://catalog.data.gov/dataset/tiger-line-shapefile-2016-nation-u-s-primary-roads-national-shapefile
  - Primary roads national shapefile

### Truck Parking (Jason's Law Data)
- FHWA Jason's Law Survey:
  https://ops.fhwa.dot.gov/freight/infrastructure/truck_parking/jasons_law/truckparkingsurvey/
  - Comprehensive truck parking survey with locations, volumes, capacity
  - PDF Report (19.6 MB):
    https://ops.fhwa.dot.gov/freight/infrastructure/truck_parking/jasons_law/truckparkingsurvey/jasons_law.pdf
  - 2015 baseline + 2018-2019 update
  - ~2,000 public and ~27,000 private truck parking spaces documented

- FHWA Truck Parking Hub:
  https://ops.fhwa.dot.gov/freight/infrastructure/truck_parking/index.htm

=============================================================================
COMMERCIAL/PRIVATE APIs
=============================================================================

### Love's Travel Stops
- Developer Portal: https://developer.loves.com/
  - Official API access for location data
  - REST, SOAP, AsyncAPIs available

### Pilot Flying J
- No public API
- Location Finder: https://locations.pilotflyingj.com/
- 750+ locations across North America
- Uses MuleSoft Anypoint Platform internally

### Third-Party Data (Paid)
- ScrapeHero: https://www.scrapehero.com/store/product/pilot-flying-j-locations-in-the-usa/
  - Pre-scraped Pilot Flying J locations
- AllStays: https://www.allstays.com/c/pilot-locations.htm
  - Truck stop directory

=============================================================================
OPENSTREETMAP (Free, Crowdsourced)
=============================================================================

Overpass Turbo: https://overpass-turbo.eu/

Example queries for truck stops and rest areas:

```
// Truck stops (fuel stations accepting HGV/trucks)
[out:json][timeout:60];
(
  node["amenity"="fuel"]["hgv"="yes"]({{bbox}});
  way["amenity"="fuel"]["hgv"="yes"]({{bbox}});
);
out body;

// Service areas / rest stops
[out:json][timeout:60];
(
  node["highway"="services"]({{bbox}});
  way["highway"="services"]({{bbox}});
  node["highway"="rest_area"]({{bbox}});
  way["highway"="rest_area"]({{bbox}});
);
out body;

// All fuel stations in a state (e.g., Texas)
[out:json][timeout:120];
area["name"="Texas"]["admin_level"="4"]->.searchArea;
(
  node["amenity"="fuel"](area.searchArea);
  way["amenity"="fuel"](area.searchArea);
);
out body;
```

Export as GeoJSON for analysis.

OSM Tags Reference:
- amenity=fuel: Fuel/gas stations
- highway=services: Service areas (rest stops with amenities)
- highway=rest_area: Rest areas (basic facilities)
- hgv=yes: Accepts heavy goods vehicles (trucks)

=============================================================================
RECOMMENDED APPROACH FOR ML
=============================================================================

For richest dataset:
1. Jason's Law survey data (official truck parking with capacity)
2. OpenStreetMap via Overpass (fuel stations, rest areas, service areas)
3. TIGER/Line for road network geometry
4. NTAD for traffic volumes and road classifications

Output files (to be written to ./data/):
    - truck_stops.parquet: Truck stop locations with amenities
    - rest_areas.parquet: Rest area locations
    - interstate_network.parquet: Interstate highway segments
    - truck_parking_capacity.parquet: Jason's Law parking data

Dependencies:
    pip install requests pandas pyarrow geopandas shapely overpy

Usage:
    python download_road_data.py [--output-dir ./data]
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def download_osm_truck_stops(bbox: Optional[tuple] = None, area_name: str = "United States") -> pd.DataFrame:
    """
    Download truck stops from OpenStreetMap using Overpass API.

    Args:
        bbox: Optional bounding box (south, west, north, east)
        area_name: Area name for query (default: "United States")

    Returns:
        DataFrame with truck stop locations
    """
    try:
        import overpy
    except ImportError:
        logger.error("overpy not installed. Run: pip install overpy")
        return pd.DataFrame()

    api = overpy.Overpass()

    # Query for fuel stations that accept trucks
    if bbox:
        south, west, north, east = bbox
        bbox_str = f"({south},{west},{north},{east})"
        query = f"""
        [out:json][timeout:300];
        (
          node["amenity"="fuel"]["hgv"="yes"]{bbox_str};
          way["amenity"="fuel"]["hgv"="yes"]{bbox_str};
          node["highway"="services"]{bbox_str};
          way["highway"="services"]{bbox_str};
        );
        out center;
        """
    else:
        query = f"""
        [out:json][timeout:600];
        area["name"="{area_name}"]["admin_level"="2"]->.searchArea;
        (
          node["amenity"="fuel"]["hgv"="yes"](area.searchArea);
          way["amenity"="fuel"]["hgv"="yes"](area.searchArea);
          node["highway"="services"](area.searchArea);
          way["highway"="services"](area.searchArea);
        );
        out center;
        """

    logger.info(f"Querying OSM for truck stops in {area_name}...")

    try:
        result = api.query(query)
    except Exception as e:
        logger.error(f"Overpass query failed: {e}")
        return pd.DataFrame()

    records = []

    # Process nodes
    for node in result.nodes:
        records.append({
            'osm_id': node.id,
            'osm_type': 'node',
            'latitude': float(node.lat),
            'longitude': float(node.lon),
            'name': node.tags.get('name', ''),
            'brand': node.tags.get('brand', ''),
            'amenity': node.tags.get('amenity', ''),
            'highway': node.tags.get('highway', ''),
            'hgv': node.tags.get('hgv', ''),
            'fuel_diesel': node.tags.get('fuel:diesel', ''),
            'parking': node.tags.get('parking', ''),
            'capacity': node.tags.get('capacity', ''),
        })

    # Process ways (use center point)
    for way in result.ways:
        if way.center_lat and way.center_lon:
            records.append({
                'osm_id': way.id,
                'osm_type': 'way',
                'latitude': float(way.center_lat),
                'longitude': float(way.center_lon),
                'name': way.tags.get('name', ''),
                'brand': way.tags.get('brand', ''),
                'amenity': way.tags.get('amenity', ''),
                'highway': way.tags.get('highway', ''),
                'hgv': way.tags.get('hgv', ''),
                'fuel_diesel': way.tags.get('fuel:diesel', ''),
                'parking': way.tags.get('parking', ''),
                'capacity': way.tags.get('capacity', ''),
            })

    df = pd.DataFrame(records)
    logger.info(f"Downloaded {len(df)} truck stops/service areas from OSM")
    return df


def download_osm_rest_areas(bbox: Optional[tuple] = None, area_name: str = "United States") -> pd.DataFrame:
    """
    Download rest areas from OpenStreetMap using Overpass API.

    Args:
        bbox: Optional bounding box (south, west, north, east)
        area_name: Area name for query (default: "United States")

    Returns:
        DataFrame with rest area locations
    """
    try:
        import overpy
    except ImportError:
        logger.error("overpy not installed. Run: pip install overpy")
        return pd.DataFrame()

    api = overpy.Overpass()

    if bbox:
        south, west, north, east = bbox
        bbox_str = f"({south},{west},{north},{east})"
        query = f"""
        [out:json][timeout:300];
        (
          node["highway"="rest_area"]{bbox_str};
          way["highway"="rest_area"]{bbox_str};
        );
        out center;
        """
    else:
        query = f"""
        [out:json][timeout:600];
        area["name"="{area_name}"]["admin_level"="2"]->.searchArea;
        (
          node["highway"="rest_area"](area.searchArea);
          way["highway"="rest_area"](area.searchArea);
        );
        out center;
        """

    logger.info(f"Querying OSM for rest areas in {area_name}...")

    try:
        result = api.query(query)
    except Exception as e:
        logger.error(f"Overpass query failed: {e}")
        return pd.DataFrame()

    records = []

    for node in result.nodes:
        records.append({
            'osm_id': node.id,
            'osm_type': 'node',
            'latitude': float(node.lat),
            'longitude': float(node.lon),
            'name': node.tags.get('name', ''),
            'toilets': node.tags.get('toilets', ''),
            'drinking_water': node.tags.get('drinking_water', ''),
            'picnic_table': node.tags.get('picnic_table', ''),
        })

    for way in result.ways:
        if way.center_lat and way.center_lon:
            records.append({
                'osm_id': way.id,
                'osm_type': 'way',
                'latitude': float(way.center_lat),
                'longitude': float(way.center_lon),
                'name': way.tags.get('name', ''),
                'toilets': way.tags.get('toilets', ''),
                'drinking_water': way.tags.get('drinking_water', ''),
                'picnic_table': way.tags.get('picnic_table', ''),
            })

    df = pd.DataFrame(records)
    logger.info(f"Downloaded {len(df)} rest areas from OSM")
    return df


def download_tiger_roads(output_dir: Path) -> Optional[Path]:
    """
    Download TIGER/Line primary roads shapefile.

    Note: This is a large file (~100MB compressed).

    Returns:
        Path to downloaded shapefile, or None if failed
    """
    import requests
    import zipfile
    import io

    # TIGER/Line 2023 primary roads
    url = "https://www2.census.gov/geo/tiger/TIGER2023/PRIMARYROADS/tl_2023_us_primaryroads.zip"

    output_path = output_dir / "tiger_primary_roads"
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading TIGER/Line primary roads from {url}...")

    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            zf.extractall(output_path)

        logger.info(f"Extracted TIGER/Line data to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to download TIGER/Line data: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Download road and truck stop data')
    parser.add_argument('--output-dir', type=str, default='./data',
                        help='Output directory for downloaded data')
    parser.add_argument('--osm-truck-stops', action='store_true',
                        help='Download truck stops from OpenStreetMap')
    parser.add_argument('--osm-rest-areas', action='store_true',
                        help='Download rest areas from OpenStreetMap')
    parser.add_argument('--tiger-roads', action='store_true',
                        help='Download TIGER/Line primary roads')
    parser.add_argument('--all', action='store_true',
                        help='Download all available data')
    parser.add_argument('--state', type=str, default=None,
                        help='Limit OSM queries to a specific US state (e.g., "Texas")')
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    area_name = args.state if args.state else "United States"

    if args.osm_truck_stops or args.all:
        df = download_osm_truck_stops(area_name=area_name)
        if not df.empty:
            output_path = output_dir / "truck_stops.parquet"
            df.to_parquet(output_path, index=False)
            logger.info(f"Saved {len(df)} truck stops to {output_path}")

    if args.osm_rest_areas or args.all:
        df = download_osm_rest_areas(area_name=area_name)
        if not df.empty:
            output_path = output_dir / "rest_areas.parquet"
            df.to_parquet(output_path, index=False)
            logger.info(f"Saved {len(df)} rest areas to {output_path}")

    if args.tiger_roads or args.all:
        download_tiger_roads(output_dir)

    if not any([args.osm_truck_stops, args.osm_rest_areas, args.tiger_roads, args.all]):
        logger.info("No data sources specified. Use --help for options.")
        logger.info("Example: python download_road_data.py --all --state Texas")


if __name__ == '__main__':
    main()
