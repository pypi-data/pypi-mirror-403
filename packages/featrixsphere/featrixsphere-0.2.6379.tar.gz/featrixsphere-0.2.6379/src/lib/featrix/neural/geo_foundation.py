#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
GeoFoundationEncoder: Pre-trained geographic embeddings with singleton data loading.

This module provides foundation embeddings for geographic types (ZIP codes, FIPS codes,
lat/long coordinates) that encode world knowledge like:
- Geographic proximity (nearby ZIP codes have similar embeddings)
- Administrative hierarchy (county → state relationships)
- Population density and urban/rural characteristics
- Historical weather data (when date is provided)

The data is loaded ONCE and shared across all GeoFoundationEncoder instances.

Usage:
    # First call loads data, subsequent calls reuse it
    encoder1 = GeoFoundationEncoder(d_model=128)  # Loads data
    encoder2 = GeoFoundationEncoder(d_model=128)  # Reuses loaded data

    # Encode ZIP codes
    embeddings = encoder1.encode_zip_codes(['90210', '10001', '02134'])

    # Encode FIPS codes with weather for specific dates
    embeddings = encoder1.encode_fips_codes(
        ['06037', '36061'],
        dates=['2024-01-15', '2024-01-15']
    )
"""
import logging
import math
import os
import threading
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


# =============================================================================
# Singleton Data Manager - loads data once, shared across all encoders
# =============================================================================

class _GeoDataManager:
    """Singleton manager for geographic foundation data.

    Loads parquet files once and provides thread-safe access to all encoders.
    """

    _instance: Optional["_GeoDataManager"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                # Double-check inside lock
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return

        self._initialized = True
        self._data_loaded = False
        self._data_lock = threading.Lock()

        # Data frames (loaded lazily)
        self._zip_locations = None
        self._county_locations = None
        self._state_locations = None
        self._zip_to_county_df = None
        self._intl_postal = None

        # Lookup dictionaries (built after loading)
        self._zip_to_latlong: Dict[str, Tuple[float, float]] = {}
        self._county_to_latlong: Dict[str, Tuple[float, float]] = {}
        self._state_to_latlong: Dict[str, Tuple[float, float]] = {}
        self._zip_to_county_map: Dict[str, str] = {}
        self._intl_to_latlong: Dict[str, Tuple[float, float]] = {}

        # Data directory (can be overridden)
        self._data_dir: Optional[Path] = None

    def set_data_dir(self, data_dir: Union[str, Path]) -> None:
        """Set the directory containing foundation data files."""
        self._data_dir = Path(data_dir)
        logger.info(f"GeoDataManager: data directory set to {self._data_dir}")

    def _get_data_dir(self) -> Path:
        """Get the data directory, with fallback search."""
        if self._data_dir is not None:
            return self._data_dir

        # Search in common locations
        search_paths = [
            # Relative to this file
            Path(__file__).parent.parent / 'download-data' / 'data',
            # Environment variable
            Path(os.environ.get('FEATRIX_GEO_DATA_DIR', '/nonexistent')),
            # Installed location
            Path('/opt/featrix/data/geo'),
            # Development location
            Path.home() / '.featrix' / 'geo_data',
        ]

        for path in search_paths:
            if path.exists() and (path / 'zip_locations.parquet').exists():
                self._data_dir = path
                logger.info(f"GeoDataManager: found data at {path}")
                return path

        raise FileNotFoundError(
            "Geographic foundation data not found. Run download_geographic_data.py first, "
            "or set FEATRIX_GEO_DATA_DIR environment variable."
        )

    def ensure_loaded(self) -> None:
        """Ensure data is loaded (thread-safe, loads once)."""
        if self._data_loaded:
            return

        with self._data_lock:
            if self._data_loaded:
                return

            self._load_data()
            self._data_loaded = True

    def _load_data(self) -> None:
        """Load all foundation data files."""
        import pandas as pd

        data_dir = self._get_data_dir()
        logger.info(f"GeoDataManager: Loading foundation data from {data_dir}")

        # Load parquet files
        zip_file = data_dir / 'zip_locations.parquet'
        county_file = data_dir / 'county_locations.parquet'
        states_file = data_dir / 'state_locations.parquet'
        crosswalk_file = data_dir / 'zip_to_county.parquet'
        intl_file = data_dir / 'intl_postal.parquet'

        if zip_file.exists():
            self._zip_locations = pd.read_parquet(zip_file)
            logger.info(f"  Loaded {len(self._zip_locations)} ZIP code records")

            # Build lookup dict
            for _, row in self._zip_locations.iterrows():
                self._zip_to_latlong[row['zip_code']] = (row['latitude'], row['longitude'])
        else:
            logger.warning(f"  ZIP locations file not found: {zip_file}")

        if county_file.exists():
            self._county_locations = pd.read_parquet(county_file)
            logger.info(f"  Loaded {len(self._county_locations)} county records")

            # Build lookup dicts (using county_key as the identifier)
            for _, row in self._county_locations.iterrows():
                self._county_to_latlong[row['county_key']] = (row['latitude'], row['longitude'])
        else:
            logger.warning(f"  County locations file not found: {county_file}")

        if states_file.exists():
            self._state_locations = pd.read_parquet(states_file)
            logger.info(f"  Loaded {len(self._state_locations)} state records")

            for _, row in self._state_locations.iterrows():
                self._state_to_latlong[row['state_abbrev']] = (row['latitude'], row['longitude'])
        else:
            logger.warning(f"  State locations file not found: {states_file}")

        if crosswalk_file.exists():
            self._zip_to_county_df = pd.read_parquet(crosswalk_file)
            logger.info(f"  Loaded {len(self._zip_to_county_df)} ZIP-to-county mappings")

            for _, row in self._zip_to_county_df.iterrows():
                self._zip_to_county_map[row['zip_code']] = row['county_key']
        else:
            logger.warning(f"  ZIP-to-county crosswalk not found: {crosswalk_file}")

        if intl_file.exists():
            self._intl_postal = pd.read_parquet(intl_file)
            logger.info(f"  Loaded {len(self._intl_postal)} international postal records")

            # Build lookup dict for international
            for _, row in self._intl_postal.iterrows():
                key = f"{row['country_code']}:{row['postal_code']}"
                self._intl_to_latlong[key] = (row['latitude'], row['longitude'])
        else:
            logger.warning(f"  International postal file not found: {intl_file}")

        logger.info("GeoDataManager: Foundation data loaded successfully")

    def get_zip_latlong(self, zip_code: str) -> Optional[Tuple[float, float]]:
        """Get lat/long for a ZIP code."""
        self.ensure_loaded()
        return self._zip_to_latlong.get(zip_code)

    def get_county_latlong(self, county_key: str) -> Optional[Tuple[float, float]]:
        """Get lat/long for a county (by county_key like 'Los Angeles County, CA')."""
        self.ensure_loaded()
        return self._county_to_latlong.get(county_key)

    def get_state_latlong(self, state_abbrev: str) -> Optional[Tuple[float, float]]:
        """Get lat/long for a state abbreviation."""
        self.ensure_loaded()
        return self._state_to_latlong.get(state_abbrev)

    def get_zip_county(self, zip_code: str) -> Optional[str]:
        """Get county_key for a ZIP code."""
        self.ensure_loaded()
        return self._zip_to_county_map.get(zip_code)

    def get_zip_state(self, zip_code: str) -> Optional[str]:
        """Get state abbreviation for a ZIP code."""
        self.ensure_loaded()
        if self._zip_locations is not None:
            match = self._zip_locations[self._zip_locations['zip_code'] == zip_code]
            if not match.empty:
                return match.iloc[0]['state_abbrev']
        return None

    def get_intl_latlong(self, country_code: str, postal_code: str) -> Optional[Tuple[float, float]]:
        """Get lat/long for an international postal code."""
        self.ensure_loaded()
        key = f"{country_code}:{postal_code}"
        return self._intl_to_latlong.get(key)

    @property
    def is_loaded(self) -> bool:
        return self._data_loaded


def get_geo_data_manager() -> _GeoDataManager:
    """Get the singleton GeoDataManager instance."""
    return _GeoDataManager()


# =============================================================================
# Singleton Weather Data Manager
# =============================================================================

class _WeatherDataManager:
    """Singleton manager for weather foundation data.

    Loads weather parquet files once and provides thread-safe access.
    Weather data is keyed by (FIPS, date) and includes tmax, tmin, tavg, prcp.
    """

    _instance: Optional["_WeatherDataManager"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return

        self._initialized = True
        self._data_loaded = False
        self._data_lock = threading.Lock()

        # Weather data by year (loaded lazily)
        self._yearly_weather: Dict[int, Optional[pd.DataFrame]] = {}

        # Climate normals
        self._normals: Optional[pd.DataFrame] = None
        self._normals_lookup: Dict[Tuple[str, int], Tuple[float, float, float, float]] = {}

        # Data directory
        self._data_dir: Optional[Path] = None

    def set_data_dir(self, data_dir: Union[str, Path]) -> None:
        """Set the directory containing weather data files."""
        self._data_dir = Path(data_dir)
        logger.info(f"WeatherDataManager: data directory set to {self._data_dir}")

    def _get_data_dir(self) -> Path:
        """Get the weather data directory."""
        if self._data_dir is not None:
            return self._data_dir

        # Search in common locations
        search_paths = [
            Path(os.environ.get('FEATRIX_WEATHER_DATA_DIR', '/nonexistent')),
            Path('/foundation_data/weather'),
            Path.home() / '.featrix' / 'weather_data',
        ]

        for path in search_paths:
            if path.exists() and any(path.glob('county_weather_*.parquet')):
                self._data_dir = path
                logger.info(f"WeatherDataManager: found data at {path}")
                return path

        logger.warning("Weather data not found. Weather features will be zeros.")
        return Path('/nonexistent')

    def _load_year(self, year: int) -> Optional[pd.DataFrame]:
        """Load weather data for a specific year."""
        if year in self._yearly_weather:
            return self._yearly_weather[year]

        data_dir = self._get_data_dir()
        year_file = data_dir / f'county_weather_{year}.parquet'

        if year_file.exists():
            df = pd.read_parquet(year_file)
            df['date'] = pd.to_datetime(df['date']).dt.date
            # Ensure FIPS is string with leading zeros
            df['fips'] = df['fips'].astype(str).str.zfill(5)
            # Convert weather columns to float
            for col in ['tmax', 'tmin', 'tavg', 'prcp']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            self._yearly_weather[year] = df
            logger.debug(f"WeatherDataManager: loaded {len(df)} records for {year}")
        else:
            self._yearly_weather[year] = None
            logger.debug(f"WeatherDataManager: no data for {year}")

        return self._yearly_weather[year]

    def _load_normals(self) -> None:
        """Load climate normals (30-year averages)."""
        if self._normals is not None:
            return

        data_dir = self._get_data_dir()
        normals_file = data_dir / 'county_weather_normals.parquet'

        if normals_file.exists():
            self._normals = pd.read_parquet(normals_file)
            self._normals['fips'] = self._normals['fips'].astype(str).str.zfill(5)

            # Build lookup dict: (fips, month) -> (tmax_normal, tmin_normal, tavg_normal, prcp_normal)
            for _, row in self._normals.iterrows():
                key = (row['fips'], int(row['month']))
                self._normals_lookup[key] = (
                    float(row.get('tmax_normal', 0) or 0),
                    float(row.get('tmin_normal', 0) or 0),
                    float(row.get('tavg_normal', 0) or 0),
                    float(row.get('prcp_daily_normal', 0) or 0),
                )
            logger.info(f"WeatherDataManager: loaded {len(self._normals_lookup)} climate normals")
        else:
            logger.warning(f"Climate normals not found: {normals_file}")

    def get_weather(
        self,
        fips: str,
        dt: Union[date, datetime, pd.Timestamp, str],
    ) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
        """Get weather for a FIPS code and date.

        Args:
            fips: 5-digit FIPS county code
            dt: Date

        Returns:
            Tuple of (tmax, tmin, tavg, prcp) or (None, None, None, None) if not found
        """
        # Parse date
        if isinstance(dt, str):
            dt = pd.to_datetime(dt).date()
        elif isinstance(dt, datetime):
            dt = dt.date()
        elif isinstance(dt, pd.Timestamp):
            dt = dt.date()

        # Normalize FIPS
        fips = str(fips).zfill(5)

        # Load year data
        year = dt.year
        weather_df = self._load_year(year)

        if weather_df is None:
            return (None, None, None, None)

        # Find matching row
        mask = (weather_df['fips'] == fips) & (weather_df['date'] == dt)
        matches = weather_df[mask]

        if matches.empty:
            return (None, None, None, None)

        row = matches.iloc[0]
        return (
            row['tmax'] if pd.notna(row['tmax']) else None,
            row['tmin'] if pd.notna(row['tmin']) else None,
            row['tavg'] if pd.notna(row['tavg']) else None,
            row['prcp'] if pd.notna(row['prcp']) else None,
        )

    def get_climate_normal(
        self,
        fips: str,
        month: int,
    ) -> Tuple[float, float, float, float]:
        """Get climate normal for a FIPS code and month.

        Args:
            fips: 5-digit FIPS county code
            month: Month (1-12)

        Returns:
            Tuple of (tmax_normal, tmin_normal, tavg_normal, prcp_normal)
            Returns (0, 0, 0, 0) if not found.
        """
        self._load_normals()
        fips = str(fips).zfill(5)
        return self._normals_lookup.get((fips, month), (0.0, 0.0, 0.0, 0.0))

    def get_weather_with_anomaly(
        self,
        fips: str,
        dt: Union[date, datetime, pd.Timestamp, str],
    ) -> Dict[str, Optional[float]]:
        """Get weather with anomaly from climate normal.

        Args:
            fips: 5-digit FIPS county code
            dt: Date

        Returns:
            Dict with tmax, tmin, tavg, prcp and their anomalies
        """
        tmax, tmin, tavg, prcp = self.get_weather(fips, dt)

        # Parse date for month
        if isinstance(dt, str):
            dt = pd.to_datetime(dt).date()
        elif isinstance(dt, datetime):
            dt = dt.date()
        elif isinstance(dt, pd.Timestamp):
            dt = dt.date()

        month = dt.month
        norm_tmax, norm_tmin, norm_tavg, norm_prcp = self.get_climate_normal(fips, month)

        return {
            'tmax': tmax,
            'tmin': tmin,
            'tavg': tavg,
            'prcp': prcp,
            'tmax_anomaly': (tmax - norm_tmax) if tmax is not None else None,
            'tmin_anomaly': (tmin - norm_tmin) if tmin is not None else None,
            'tavg_anomaly': (tavg - norm_tavg) if tavg is not None else None,
            'prcp_anomaly': (prcp - norm_prcp) if prcp is not None else None,
        }


def get_weather_data_manager() -> _WeatherDataManager:
    """Get the singleton WeatherDataManager instance."""
    return _WeatherDataManager()


# =============================================================================
# GeoFoundationEncoder - Neural encoder using foundation data
# =============================================================================

class GeoFoundationEncoder(nn.Module):
    """Foundation encoder for geographic + temporal + weather embeddings.

    Encodes a unified representation combining:
    - Geographic coordinates (lat/long with cyclical encoding)
    - Administrative hierarchy (ZIP → County/FIPS → State)
    - Temporal features (date with cyclical day/month/year encoding)
    - Weather features (tmax, tmin, tavg, prcp + anomalies from normals)

    The embedding captures "what was the weather like at this location on this date"
    which is valuable for many prediction tasks (retail, energy, agriculture, etc.).

    Multiple instances share the same underlying data through singleton managers.

    Usage:
        encoder = GeoFoundationEncoder(d_model=128, include_weather=True)

        # Encode with all features
        embeddings = encoder.encode(
            locations=['90210', '10001'],
            location_type='zip',
            dates=['2024-01-15', '2024-07-04'],
        )

        # Or encode location only (no date/weather)
        embeddings = encoder.encode_zip_codes(['90210', '10001'])
    """

    def __init__(
        self,
        d_model: int,
        n_coordinate_buckets: int = 100,
        use_cyclical_encoding: bool = True,
        include_weather: bool = True,
    ):
        """
        Args:
            d_model: Output embedding dimension
            n_coordinate_buckets: Number of buckets for discretized lat/long
            use_cyclical_encoding: Use sin/cos encoding for coordinates
            include_weather: Include weather features when date is provided
        """
        super().__init__()
        self.d_model = d_model
        self.n_coordinate_buckets = n_coordinate_buckets
        self.use_cyclical_encoding = use_cyclical_encoding
        self.include_weather = include_weather

        # Get shared data managers
        self._geo_manager = get_geo_data_manager()
        self._weather_manager = get_weather_data_manager() if include_weather else None

        # --- Coordinate encoding ---
        if use_cyclical_encoding:
            coord_dim = 4  # sin/cos for lat and long
        else:
            coord_dim = 2

        # Learned embeddings for bucketized coordinates
        self.lat_embedding = nn.Embedding(n_coordinate_buckets, d_model // 4)
        self.long_embedding = nn.Embedding(n_coordinate_buckets, d_model // 4)

        proj_input_dim = coord_dim + (d_model // 4) * 2
        self.coord_projection = nn.Sequential(
            nn.Linear(proj_input_dim, d_model // 2),
            nn.ReLU(),
            nn.Linear(d_model // 2, d_model // 2),
        )

        # --- State embedding ---
        # 60 = 50 states + DC + territories + unknown
        self.state_embedding = nn.Embedding(60, d_model // 4)

        # --- Date/temporal encoding ---
        # Cyclical encoding for day-of-year (captures seasonality)
        # 8 dims: sin/cos for day_of_year, month, day_of_week, year_progress
        self.date_dim = 8

        # --- Weather encoding ---
        # 8 features: tmax, tmin, tavg, prcp, tmax_anomaly, tmin_anomaly, tavg_anomaly, prcp_anomaly
        self.weather_dim = 8 if include_weather else 0

        self.weather_projection = nn.Sequential(
            nn.Linear(self.weather_dim, d_model // 4),
            nn.ReLU(),
            nn.Linear(d_model // 4, d_model // 4),
        ) if include_weather else None

        # --- Final fusion ---
        # Inputs: coord (d_model//2) + state (d_model//4) + date (8) + weather (d_model//4 or 0)
        fusion_input = (d_model // 2) + (d_model // 4) + self.date_dim
        if include_weather:
            fusion_input += d_model // 4

        self.fusion = nn.Sequential(
            nn.Linear(fusion_input, d_model),
            nn.ReLU(),
            nn.LayerNorm(d_model),
        )

        # Unknown location embedding
        self.unknown_embedding = nn.Parameter(torch.randn(d_model) * 0.02)

        logger.debug(
            f"GeoFoundationEncoder initialized: d_model={d_model}, "
            f"include_weather={include_weather}"
        )

    def _normalize_zip(self, zip_code: str) -> str:
        """Normalize ZIP code to 5-digit format."""
        # Strip whitespace
        zip_code = str(zip_code).strip()

        # Handle ZIP+4 format
        if '-' in zip_code:
            zip_code = zip_code.split('-')[0]

        # Pad with leading zeros
        return zip_code.zfill(5)

    def _encode_coordinates(
        self,
        lat: torch.Tensor,
        long: torch.Tensor,
    ) -> torch.Tensor:
        """Encode lat/long coordinates.

        Args:
            lat: Latitude values (batch,)
            long: Longitude values (batch,)

        Returns:
            Coordinate embeddings (batch, d_model)
        """
        batch_size = lat.shape[0]
        device = lat.device

        # Cyclical encoding for periodicity
        if self.use_cyclical_encoding:
            # Normalize to [0, 2π]
            lat_norm = (lat + 90) / 180 * 2 * math.pi
            long_norm = (long + 180) / 360 * 2 * math.pi

            coord_features = torch.stack([
                torch.sin(lat_norm),
                torch.cos(lat_norm),
                torch.sin(long_norm),
                torch.cos(long_norm),
            ], dim=-1)  # (batch, 4)
        else:
            # Direct normalization to [-1, 1]
            lat_norm = lat / 90
            long_norm = long / 180
            coord_features = torch.stack([lat_norm, long_norm], dim=-1)  # (batch, 2)

        # Bucketize for learned embeddings
        lat_bucket = ((lat + 90) / 180 * (self.n_coordinate_buckets - 1)).long().clamp(0, self.n_coordinate_buckets - 1)
        long_bucket = ((long + 180) / 360 * (self.n_coordinate_buckets - 1)).long().clamp(0, self.n_coordinate_buckets - 1)

        lat_emb = self.lat_embedding(lat_bucket)  # (batch, d_model//4)
        long_emb = self.long_embedding(long_bucket)  # (batch, d_model//4)

        # Concatenate and project
        combined = torch.cat([coord_features, lat_emb, long_emb], dim=-1)
        return self.coord_projection(combined)

    def _state_abbrev_to_idx(self, state_abbrev: Optional[str]) -> int:
        """Convert state abbreviation to embedding index."""
        if not state_abbrev:
            return 0
        # Map state abbreviations to indices 1-56 (0 = unknown)
        state_order = [
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL',
            'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME',
            'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH',
            'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI',
            'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI',
            'WY', 'AS', 'GU', 'MP', 'PR', 'VI',
        ]
        try:
            return state_order.index(state_abbrev) + 1
        except ValueError:
            return 0

    def encode_zip_codes(
        self,
        zip_codes: List[str],
        device: Optional[torch.device] = None,
    ) -> torch.Tensor:
        """Encode a batch of ZIP codes to embeddings.

        Args:
            zip_codes: List of ZIP code strings
            device: Target device for output tensor

        Returns:
            Embeddings of shape (batch, d_model)
        """
        if device is None:
            device = next(self.parameters()).device

        embeddings = []

        for zip_code in zip_codes:
            zip_norm = self._normalize_zip(zip_code)
            latlong = self._data_manager.get_zip_latlong(zip_norm)

            if latlong is None:
                # Unknown ZIP - use learned unknown embedding
                embeddings.append(self.unknown_embedding)
            else:
                lat, long = latlong

                # Get coordinate embedding
                lat_t = torch.tensor([lat], device=device, dtype=torch.float32)
                long_t = torch.tensor([long], device=device, dtype=torch.float32)
                coord_emb = self._encode_coordinates(lat_t, long_t).squeeze(0)

                # Get state embedding
                state_abbrev = self._data_manager.get_zip_state(zip_norm)
                state_idx = self._state_abbrev_to_idx(state_abbrev)

                state_emb = self.state_embedding(torch.tensor([state_idx], device=device)).squeeze(0)

                # Urban/rural (placeholder - would need additional data)
                urban_rural_emb = self.urban_rural_embedding(torch.tensor([0], device=device)).squeeze(0)

                # Fuse all features
                combined = torch.cat([coord_emb, state_emb, urban_rural_emb])
                fused = self.fusion(combined.unsqueeze(0)).squeeze(0)
                embeddings.append(fused)

        return torch.stack(embeddings, dim=0)

    def encode_counties(
        self,
        county_keys: List[str],
        device: Optional[torch.device] = None,
    ) -> torch.Tensor:
        """Encode a batch of county keys to embeddings.

        Args:
            county_keys: List of county key strings like "Los Angeles County, CA"
            device: Target device for output tensor

        Returns:
            Embeddings of shape (batch, d_model)
        """
        if device is None:
            device = next(self.parameters()).device

        embeddings = []

        for county_key in county_keys:
            latlong = self._data_manager.get_county_latlong(county_key)

            if latlong is None:
                embeddings.append(self.unknown_embedding)
            else:
                lat, long = latlong

                # Coordinate embedding
                lat_t = torch.tensor([lat], device=device, dtype=torch.float32)
                long_t = torch.tensor([long], device=device, dtype=torch.float32)
                coord_emb = self._encode_coordinates(lat_t, long_t).squeeze(0)

                # Extract state from county key (e.g., "Los Angeles County, CA" -> "CA")
                state_abbrev = county_key.split(', ')[-1] if ', ' in county_key else None
                state_idx = self._state_abbrev_to_idx(state_abbrev)

                state_emb = self.state_embedding(torch.tensor([state_idx], device=device)).squeeze(0)
                urban_rural_emb = self.urban_rural_embedding(torch.tensor([0], device=device)).squeeze(0)

                combined = torch.cat([coord_emb, state_emb, urban_rural_emb])
                fused = self.fusion(combined.unsqueeze(0)).squeeze(0)
                embeddings.append(fused)

        return torch.stack(embeddings, dim=0)

    def encode_latlong(
        self,
        coordinates: List[Tuple[float, float]],
        device: Optional[torch.device] = None,
    ) -> torch.Tensor:
        """Encode raw lat/long coordinates to embeddings.

        Args:
            coordinates: List of (latitude, longitude) tuples
            device: Target device for output tensor

        Returns:
            Embeddings of shape (batch, d_model)
        """
        if device is None:
            device = next(self.parameters()).device

        lats = torch.tensor([c[0] for c in coordinates], device=device, dtype=torch.float32)
        longs = torch.tensor([c[1] for c in coordinates], device=device, dtype=torch.float32)

        coord_emb = self._encode_coordinates(lats, longs)

        # For raw coordinates, we don't have state info
        # Use zero state embedding
        batch_size = len(coordinates)
        state_emb = self.state_embedding(torch.zeros(batch_size, device=device, dtype=torch.long))
        urban_rural_emb = self.urban_rural_embedding(torch.zeros(batch_size, device=device, dtype=torch.long))

        combined = torch.cat([coord_emb, state_emb, urban_rural_emb], dim=-1)
        return self.fusion(combined)

    def forward(
        self,
        values: List[str],
        geo_type: str = 'zip',
        device: Optional[torch.device] = None,
    ) -> torch.Tensor:
        """Forward pass - encode geographic values.

        Args:
            values: List of geographic values (ZIP codes, county keys, etc.)
            geo_type: Type of geographic data ('zip', 'county', 'latlong')
            device: Target device

        Returns:
            Embeddings of shape (batch, d_model)
        """
        if geo_type == 'zip':
            return self.encode_zip_codes(values, device)
        elif geo_type == 'county':
            return self.encode_counties(values, device)
        elif geo_type == 'latlong':
            # Parse "lat,long" strings
            coordinates = []
            for v in values:
                parts = str(v).split(',')
                if len(parts) == 2:
                    try:
                        coordinates.append((float(parts[0]), float(parts[1])))
                    except ValueError:
                        coordinates.append((0.0, 0.0))  # Invalid
                else:
                    coordinates.append((0.0, 0.0))
            return self.encode_latlong(coordinates, device)
        else:
            raise ValueError(f"Unknown geo_type: {geo_type}")
