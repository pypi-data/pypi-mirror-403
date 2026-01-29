#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential.  Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
#
import argparse
import asyncio
import logging
import sys
import traceback
import sqlite3

import pandas as pd

from pathlib import Path
from collections import Counter
import os
import pickle
from pandas import DataFrame

try:
    from featrix.neural import device
except ModuleNotFoundError:
    p = Path(__file__).parent
    while p.stem != "featrix":
        p = p.parent
    sys.path.insert(0, str(p.parent))
    from featrix.neural import device


logger = logging.getLogger(__name__)

# def file_is_sqlite_db(path):
#     return ...

def check_sqlite_header(file_path):
    # SQLite header is 16 bytes long and starts with "SQLite format 3"
    sqlite_header = b"SQLite format 3\000"
    
    try:
        with open(file_path, 'rb') as file:
            header = file.read(16)      # assumes > 16 bytes long file.
            return header == sqlite_header
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def sqlite_get_columns_for_table(cursor, table_name):
    # cursor = sqlite_connection.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns_info = cursor.fetchall()
    column_names = [column[1] for column in columns_info]
    return column_names


def load_sqlite_to_df(sqlite_connection, sqlite_table_select):
    assert sqlite_connection is not None, "sqlite_connection should not be None"
    assert sqlite_table_select is not None, "sqlite_table_select must be specified when using SQLite (e.g., SELECT * from data)"
    
    cursor = sqlite_connection.cursor()

    sql_cols = sqlite_get_columns_for_table(cursor, "data")
    embed_cols = []
    reg_cols = []
    for c in sql_cols:
        if c.endswith("_embedding"):
            embed_cols.append(c)
        else:
            reg_cols.append(c)
    
    df = pd.read_sql(f"SELECT * from data", sqlite_connection)
    for c in embed_cols:
        def blob_to_vec(blob):
            if blob is None:
                return None
            if blob != blob:
                return blob
            try:
                blob = pickle.loads(blob)
                
                if blob is None:
                    return None
                assert type(blob) == list
                return blob
            except Exception as ex:
                traceback.print_exc()
                raise ex
            
        df[c] = df[c].apply(blob_to_vec)
    logger.info(f"Final columns: {df.columns}")
    #df = pd.read_sql(sqlite_table_select, sqlite_connection)
    return df


def is_foundation_sqlite(sqlite_connection) -> bool:
    """
    Check if a SQLite database is a foundation database.

    Foundation databases have: train, validation, column_types tables
    Standard databases have: data table
    """
    cursor = sqlite_connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = set(row[0] for row in cursor.fetchall())

    # Foundation database must have train, validation, and column_types
    foundation_tables = {'train', 'validation', 'column_types'}
    return foundation_tables.issubset(tables)


def load_foundation_sqlite_to_df(sqlite_connection, split: str = 'train'):
    """
    Load data from a foundation SQLite database.

    Foundation databases have separate tables: warmup, train, validation, test
    This function loads from the specified split table.

    Args:
        sqlite_connection: SQLite connection
        split: Which split to load ('train', 'validation', 'test', 'warmup')

    Returns:
        DataFrame with the split data
    """
    valid_splits = ['train', 'validation', 'test', 'warmup']
    if split not in valid_splits:
        raise ValueError(f"Invalid split '{split}'. Must be one of: {valid_splits}")

    cursor = sqlite_connection.cursor()

    # Check if table exists
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (split,))
    if not cursor.fetchone():
        raise ValueError(f"Foundation database does not have '{split}' table")

    # Get column names (exclude row_idx which is internal)
    cursor.execute(f"PRAGMA table_info({split})")
    columns_info = cursor.fetchall()
    column_names = [col[1] for col in columns_info if col[1] != 'row_idx']

    # Load data
    cols_sql = ', '.join(f'"{c}"' for c in column_names)
    df = pd.read_sql(f"SELECT {cols_sql} FROM {split}", sqlite_connection)

    logger.info(f"📊 Loaded {len(df):,} rows from foundation '{split}' table ({len(df.columns)} columns)")
    return df


def load_sqlite_file_to_df(transient_upload_file_name):

    sqlite_table_select = "SELECT * FROM data"
    sqlite_db_file = str(transient_upload_file_name)
    sqlite_data_source = None

    logger.info(f"sqlite_db_file == __{sqlite_db_file}__")
    if sqlite_db_file is not None:
        files_to_try = [sqlite_db_file, sqlite_db_file + ".sqlite3.gz"]
        for f in files_to_try:
            if os.path.exists(f):
                logger.info(f"found file {f}...")
                if f.endswith(".gz"):
                    logger.info(f".... unzipping {f}")
                    rc = os.system(f"gunzip -f \"{f}\"")
                    logger.info(f"gunzip returned {rc}")
                    assert rc == 0, "Failed to gunzip data"
                    f = f[:-3]  # chop .gz
                # Open SQLite read only
                real_path = os.path.realpath(f)
                logger.info(f"real path = __{real_path}__")
                sqlite_data_source = sqlite3.connect(f'file:///{real_path}?mode=ro', uri=True)
                sqlite_db_file = f
            else:
                logger.info(f"file {f} does not exist")
        assert sqlite_data_source is not None, "couldn't find a sqlite db"
    logger.info(f"sqlite_data_source = {sqlite_data_source}")

    # Check if this is a foundation database
    if is_foundation_sqlite(sqlite_data_source):
        logger.info("📊 Detected FOUNDATION SQLite database - loading train split")
        use_df = load_foundation_sqlite_to_df(sqlite_data_source, split='train')
    else:
        # Standard database with 'data' table
        use_df = load_sqlite_to_df(sqlite_connection=sqlite_data_source,
                                    sqlite_table_select=sqlite_table_select)

    # Log columns found after SQLite loading for debugging (same format as CSV logging)
    if use_df is not None:
        logger.info(f"📋 Columns found in SQLite ({len(use_df.columns)} total): {list(use_df.columns)[:50]}{'...' if len(use_df.columns) > 50 else ''}")
        if len(use_df.columns) > 50:
            logger.info(f"   ... and {len(use_df.columns) - 50} more columns")

    return use_df


def load_sqlite_table_to_df(sqlite_db_path: str, table_name: str):
    """
    Load data from a specific table in a SQLite database.

    Used for loading visualization data from 'training_animation_data' table
    for epoch projections.

    Args:
        sqlite_db_path: Path to the SQLite database file
        table_name: Name of the table to load from

    Returns:
        DataFrame with table contents, or None if table doesn't exist
    """
    import os
    import sqlite3
    import pandas as pd

    if not os.path.exists(sqlite_db_path):
        logger.warning(f"SQLite database not found: {sqlite_db_path}")
        return None

    try:
        real_path = os.path.realpath(sqlite_db_path)
        conn = sqlite3.connect(f'file:///{real_path}?mode=ro', uri=True)

        # Check if table exists
        cursor = conn.cursor()
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            logger.info(f"Table '{table_name}' not found in {sqlite_db_path}")
            conn.close()
            return None

        # Load data from table
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        conn.close()

        logger.info(f"📋 Loaded {len(df)} rows from '{table_name}' table ({len(df.columns)} columns)")
        return df

    except Exception as e:
        logger.error(f"Error loading table '{table_name}' from {sqlite_db_path}: {e}")
        return None

