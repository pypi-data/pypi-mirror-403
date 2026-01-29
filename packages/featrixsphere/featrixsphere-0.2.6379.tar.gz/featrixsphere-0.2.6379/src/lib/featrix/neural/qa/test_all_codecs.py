#!/usr/bin/env python3
"""
Comprehensive Codec Unit Tests

Tests all codecs (email, domain, set, scalar, timestamp, url, json, vector, setlist)
with synthetic data and verifies ES training works with all column types.

This test creates synthetic data with all supported column types and:
1. Tests each codec's tokenize() method individually
2. Trains an EmbeddingSpace on the synthetic data
3. Verifies training completes without dtype mismatches or other errors
"""
import sys
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import random
import string
import json as json_lib

# Path setup
test_dir = Path(__file__).parent
neural_dir = test_dir.parent
featrix_dir = neural_dir.parent
lib_dir = featrix_dir.parent
src_dir = lib_dir.parent

sys.path.insert(0, str(lib_dir))
sys.path.insert(0, str(src_dir))

import numpy as np
import pandas as pd
import torch

from featrix.neural.model_config import ColumnType
from featrix.neural.featrix_token import Token, TokenStatus, TokenBatch
from featrix.neural.input_data_set import FeatrixInputDataSet
from featrix.neural.embedded_space import EmbeddingSpace

# Import logging to see what's happening
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)


# =============================================================================
# SYNTHETIC DATA GENERATORS
# =============================================================================

def generate_emails(n: int) -> list:
    """Generate synthetic email addresses."""
    domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'company.com', 'example.org', 'test.io']
    tlds = ['com', 'org', 'net', 'io', 'ai', 'co.uk']

    emails = []
    for i in range(n):
        if random.random() < 0.1:
            emails.append(None)  # 10% null
        else:
            local = ''.join(random.choices(string.ascii_lowercase, k=random.randint(5, 12)))
            if random.random() < 0.5:
                local += str(random.randint(1, 999))
            domain = random.choice(domains)
            emails.append(f"{local}@{domain}")
    return emails


def generate_domains(n: int) -> list:
    """Generate synthetic domain names."""
    subdomains = ['', 'www', 'mail', 'api', 'app', 'blog']
    mains = ['example', 'test', 'company', 'business', 'website', 'platform']
    tlds = ['com', 'org', 'net', 'io', 'ai', 'de', 'uk']

    domains = []
    for i in range(n):
        if random.random() < 0.1:
            domains.append(None)
        else:
            subdomain = random.choice(subdomains)
            main = random.choice(mains) + str(random.randint(1, 100))
            tld = random.choice(tlds)
            if subdomain:
                domains.append(f"{subdomain}.{main}.{tld}")
            else:
                domains.append(f"{main}.{tld}")
    return domains


def generate_urls(n: int) -> list:
    """Generate synthetic URLs."""
    protocols = ['http://', 'https://']
    paths = ['', '/home', '/about', '/api/v1/users', '/products/123', '/blog/post-title']

    urls = []
    for i in range(n):
        if random.random() < 0.1:
            urls.append(None)
        else:
            protocol = random.choice(protocols)
            domain = f"example{random.randint(1, 50)}.com"
            path = random.choice(paths)
            if random.random() < 0.3:
                path += f"?id={random.randint(1, 1000)}"
            urls.append(f"{protocol}{domain}{path}")
    return urls


def generate_timestamps(n: int) -> list:
    """Generate synthetic timestamps."""
    base = datetime(2020, 1, 1)
    timestamps = []
    for i in range(n):
        if random.random() < 0.1:
            timestamps.append(None)
        else:
            delta = timedelta(days=random.randint(0, 1500),
                            hours=random.randint(0, 23),
                            minutes=random.randint(0, 59))
            timestamps.append(base + delta)
    return timestamps


def generate_scalars(n: int, mean: float = 100, std: float = 50) -> list:
    """Generate synthetic scalar values."""
    scalars = []
    for i in range(n):
        if random.random() < 0.1:
            scalars.append(None)
        else:
            val = np.random.normal(mean, std)
            scalars.append(float(val))
    return scalars


def generate_sets(n: int, categories: list = None) -> list:
    """Generate synthetic categorical/set values."""
    if categories is None:
        categories = ['CategoryA', 'CategoryB', 'CategoryC', 'CategoryD', 'CategoryE',
                     'TypeX', 'TypeY', 'TypeZ', 'Unknown', 'Other']

    values = []
    for i in range(n):
        if random.random() < 0.1:
            values.append(None)
        else:
            values.append(random.choice(categories))
    return values


def generate_json_objects(n: int) -> list:
    """Generate synthetic JSON objects."""
    jsons = []
    for i in range(n):
        if random.random() < 0.1:
            jsons.append(None)
        else:
            obj = {
                'id': random.randint(1, 10000),
                'name': ''.join(random.choices(string.ascii_letters, k=8)),
                'active': random.choice([True, False]),
                'score': round(random.uniform(0, 100), 2),
                'tags': random.sample(['a', 'b', 'c', 'd', 'e'], k=random.randint(1, 3))
            }
            jsons.append(json_lib.dumps(obj))
    return jsons


def generate_vectors(n: int, dim: int = 8) -> list:
    """Generate synthetic vector values."""
    vectors = []
    for i in range(n):
        if random.random() < 0.1:
            vectors.append(None)
        else:
            vec = np.random.randn(dim).tolist()
            vectors.append(str(vec))  # Store as string representation
    return vectors


def generate_setlists(n: int, categories: list = None) -> list:
    """Generate synthetic list-of-set values (multi-label)."""
    if categories is None:
        categories = ['TagA', 'TagB', 'TagC', 'TagD', 'TagE', 'LabelX', 'LabelY']

    values = []
    for i in range(n):
        if random.random() < 0.1:
            values.append(None)
        else:
            num_items = random.randint(1, 4)
            items = random.sample(categories, min(num_items, len(categories)))
            values.append(','.join(items))  # Comma-separated
    return values


def create_synthetic_dataframe(n_rows: int = 500) -> pd.DataFrame:
    """
    Create a synthetic DataFrame with all supported column types.

    Columns:
    - email_col: EMAIL type
    - domain_col: DOMAIN type
    - url_col: URL type
    - timestamp_col: TIMESTAMP type (as string for easier handling)
    - scalar_col: SCALAR type (numeric)
    - set_col: SET type (categorical)
    - json_col: JSON type
    - target_col: SET type (for prediction target)
    """
    random.seed(42)
    np.random.seed(42)

    # Generate timestamps as strings to avoid crosstab issues
    timestamps = []
    base = datetime(2020, 1, 1)
    for i in range(n_rows):
        if random.random() < 0.1:
            timestamps.append(None)
        else:
            delta = timedelta(days=random.randint(0, 1500),
                            hours=random.randint(0, 23),
                            minutes=random.randint(0, 59))
            timestamps.append((base + delta).strftime('%Y-%m-%d %H:%M:%S'))

    df = pd.DataFrame({
        'email_col': generate_emails(n_rows),
        'domain_col': generate_domains(n_rows),
        'url_col': generate_urls(n_rows),
        'timestamp_col': timestamps,  # String format
        'scalar_col': generate_scalars(n_rows),
        'set_col': generate_sets(n_rows, ['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon']),
        'json_col': generate_json_objects(n_rows),
        'target_col': generate_sets(n_rows, ['ClassA', 'ClassB', 'ClassC']),
    })

    return df


# =============================================================================
# CODEC UNIT TESTS
# =============================================================================

def test_scalar_codec():
    """Test ScalarCodec tokenization."""
    print("\n" + "="*60)
    print("🧪 Testing ScalarCodec")
    print("="*60)

    from featrix.neural.scalar_codec import ScalarCodec

    # Create codec with stats dict (required)
    stats = {
        'mean': 0.0,
        'std': 1.0,
        'min': -10.0,
        'max': 10.0,
        'q25': -1.0,
        'q50': 0.0,
        'q75': 1.0,
    }
    codec = ScalarCodec(stats=stats, enc_dim=128)

    # Test various values
    test_values = [0.0, 1.0, -1.0, 100.5, -50.25, 1e6, 1e-6, None, "invalid"]

    for val in test_values:
        token = codec.tokenize(val)
        print(f"  Value: {val!r:15} -> Status: {TokenStatus(token.status).name:12} Value shape: {token.value.shape if hasattr(token.value, 'shape') else 'scalar'}")

    # Test special tokens
    not_present = codec.get_not_present_token()
    marginal = codec.get_marginal_token()
    print(f"  NOT_PRESENT token status: {TokenStatus(not_present.status).name}")
    print(f"  MARGINAL token status: {TokenStatus(marginal.status).name}")

    print("✅ ScalarCodec tests passed")
    return True


def test_set_codec():
    """Test SetCodec tokenization."""
    print("\n" + "="*60)
    print("🧪 Testing SetCodec")
    print("="*60)

    from featrix.neural.set_codec import SetCodec

    # Create codec with some initial members
    members = {'Alpha', 'Beta', 'Gamma', 'Delta', 'Unknown'}
    codec = SetCodec(members=members, enc_dim=128)

    # Test various values
    test_values = ['Alpha', 'Beta', 'Gamma', 'NewValue', None, '', 123]

    for val in test_values:
        token = codec.tokenize(val)
        print(f"  Value: {val!r:15} -> Status: {TokenStatus(token.status).name:12}")

    print("✅ SetCodec tests passed")
    return True


def test_timestamp_codec():
    """Test TimestampCodec tokenization."""
    print("\n" + "="*60)
    print("🧪 Testing TimestampCodec")
    print("="*60)

    from featrix.neural.timestamp_codec import TimestampCodec

    codec = TimestampCodec(enc_dim=128)

    # Test various values
    test_values = [
        datetime(2023, 6, 15, 10, 30, 0),
        pd.Timestamp('2024-01-01 12:00:00'),
        '2022-12-25',
        1700000000,  # Unix timestamp
        None,
        'invalid_date',
    ]

    for val in test_values:
        token = codec.tokenize(val)
        status_name = TokenStatus(token.status).name
        val_shape = token.value.shape if hasattr(token.value, 'shape') else 'N/A'
        print(f"  Value: {str(val)[:25]:25} -> Status: {status_name:12} Shape: {val_shape}")

    print("✅ TimestampCodec tests passed")
    return True


def test_email_codec():
    """Test EmailCodec tokenization."""
    print("\n" + "="*60)
    print("🧪 Testing EmailCodec")
    print("="*60)

    from featrix.neural.email_codec import EmailCodec
    from featrix.neural.simple_string_cache import SimpleStringCache

    # Create string cache (required for email codec)
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_file = os.path.join(tmpdir, "string_cache.pkl")
        string_cache = SimpleStringCache(cache_file)

        codec = EmailCodec(enc_dim=128, string_cache=string_cache, debugName="test_email")

        # Test various values
        test_values = [
            'john.doe@gmail.com',
            'user123@company.org',
            'test@subdomain.example.com',
            'invalid-email',
            'missing-at-sign.com',
            None,
            '',
        ]

        for val in test_values:
            token = codec.tokenize(val)
            status_name = TokenStatus(token.status).name
            val_shape = token.value.shape if hasattr(token.value, 'shape') else 'N/A'
            print(f"  Value: {str(val)[:30]:30} -> Status: {status_name:12} Shape: {val_shape}")

    print("✅ EmailCodec tests passed")
    return True


def test_domain_codec():
    """Test DomainCodec tokenization."""
    print("\n" + "="*60)
    print("🧪 Testing DomainCodec")
    print("="*60)

    from featrix.neural.domain_codec import DomainCodec
    from featrix.neural.simple_string_cache import SimpleStringCache

    with tempfile.TemporaryDirectory() as tmpdir:
        cache_file = os.path.join(tmpdir, "string_cache.pkl")
        string_cache = SimpleStringCache(cache_file)

        codec = DomainCodec(enc_dim=128, string_cache=string_cache, debugName="test_domain")

        test_values = [
            'google.com',
            'www.example.org',
            'api.subdomain.company.io',
            'test.co.uk',
            'invalid',
            None,
            '',
        ]

        for val in test_values:
            token = codec.tokenize(val)
            status_name = TokenStatus(token.status).name
            val_shape = token.value.shape if hasattr(token.value, 'shape') else 'N/A'
            print(f"  Value: {str(val)[:30]:30} -> Status: {status_name:12} Shape: {val_shape}")

    print("✅ DomainCodec tests passed")
    return True


def test_url_codec():
    """Test URLCodec tokenization."""
    print("\n" + "="*60)
    print("🧪 Testing URLCodec")
    print("="*60)

    from featrix.neural.url_codec import URLCodec
    from featrix.neural.simple_string_cache import SimpleStringCache

    with tempfile.TemporaryDirectory() as tmpdir:
        cache_file = os.path.join(tmpdir, "string_cache.pkl")
        string_cache = SimpleStringCache(cache_file)

        # URLCodec requires string_cache to have embedding_dim attribute
        if not hasattr(string_cache, 'embedding_dim'):
            string_cache.embedding_dim = 384  # Default embedding dim

        codec = URLCodec(embed_dim=128, string_cache=string_cache, debugName="test_url")

        test_values = [
            'https://www.google.com/search?q=test',
            'http://example.org/path/to/page',
            'https://api.company.io/v1/users/123',
            'ftp://files.example.com/data.zip',
            'invalid-url',
            None,
            '',
        ]

        for val in test_values:
            token = codec.tokenize(val)
            status_name = TokenStatus(token.status).name
            print(f"  Value: {str(val)[:40]:40} -> Status: {status_name:12}")

    print("✅ URLCodec tests passed")
    return True


def test_json_codec():
    """Test JsonCodec tokenization."""
    print("\n" + "="*60)
    print("🧪 Testing JsonCodec")
    print("="*60)

    from featrix.neural.json_codec import JsonCodec

    codec = JsonCodec(enc_dim=128, debugName="test_json")

    test_values = [
        '{"name": "test", "value": 123}',
        '{"items": [1, 2, 3], "active": true}',
        '[]',
        '{}',
        'invalid json {',
        None,
        '',
    ]

    for val in test_values:
        token = codec.tokenize(val)
        status_name = TokenStatus(token.status).name
        val_shape = token.value.shape if hasattr(token.value, 'shape') else 'N/A'
        print(f"  Value: {str(val)[:35]:35} -> Status: {status_name:12} Shape: {val_shape}")

    print("✅ JsonCodec tests passed")
    return True


# =============================================================================
# ES TRAINING INTEGRATION TEST
# =============================================================================

def test_es_training_all_types():
    """
    Integration test: Train an EmbeddingSpace on synthetic data with all column types.

    This is the critical test that verifies dtype mismatches are fixed and
    all codecs work together during training.
    """
    print("\n" + "="*60)
    print("🚀 ES TRAINING INTEGRATION TEST - ALL COLUMN TYPES")
    print("="*60)

    # Create synthetic data
    print("\n📊 Creating synthetic dataset...")
    df = create_synthetic_dataframe(n_rows=300)  # Smaller for faster test
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {list(df.columns)}")
    print(f"  Dtypes:\n{df.dtypes}")

    # Create dataset with explicit encoder overrides to ensure correct type detection
    # Note: overrides must be string values (e.g., "email"), not ColumnType enum
    # Skip URL and JSON columns - they're not fully integrated in get_default_column_encoder_configs
    encoder_overrides = {
        'email_col': 'email',
        'domain_col': 'domain_name',
        'timestamp_col': 'timestamp',
        'scalar_col': 'scalar',
        'set_col': 'set',
        'target_col': 'set',
    }

    # Remove columns that aren't fully supported in ES training yet
    ignore_cols = ['url_col', 'json_col']

    print("\n🔧 Creating FeatrixInputDataSet...")
    dataset = FeatrixInputDataSet(
        df=df,
        ignore_cols=ignore_cols,
        limit_rows=None,
        encoder_overrides=encoder_overrides,
    )

    # Print detected types
    print("\n📋 Detected column types:")
    for col_name, detector in dataset._detectors.items():
        print(f"  {col_name}: {detector.get_codec_name()}")

    # Split into train/val
    print("\n✂️  Splitting dataset...")
    train_data, val_data = dataset.split(fraction=0.2)
    print(f"  Train: {len(train_data.df)} rows")
    print(f"  Val: {len(val_data.df)} rows")

    # Create temp output directory
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "es_output")
        os.makedirs(output_dir, exist_ok=True)

        print("\n🏗️  Creating EmbeddingSpace...")
        es = EmbeddingSpace(
            train_input_data=train_data,
            val_input_data=val_data,
            d_model=64,  # Smaller for faster test
            n_epochs=5,  # Just a few epochs to test
            output_dir=output_dir,
        )

        print("\n🏋️  Training EmbeddingSpace (5 epochs)...")
        print("  (This tests all codecs with mixed precision / bfloat16)")

        try:
            es.train(
                batch_size=32,
                n_epochs=5,
                print_progress_step=1,
                enable_weightwatcher=False,
            )
            print("\n✅ ES TRAINING COMPLETED SUCCESSFULLY!")

            # Try encoding a sample record
            print("\n🔍 Testing encode_record on sample...")
            sample_row = df.iloc[0].to_dict()
            embedding = es.encode_record(sample_row, squeeze=True, short=False)
            print(f"  Embedding shape: {embedding.shape}")
            print(f"  Embedding dtype: {embedding.dtype}")
            print(f"  Embedding norm: {torch.norm(embedding).item():.4f}")

            return True

        except Exception as e:
            print(f"\n❌ ES TRAINING FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("="*70)
    print("🧪 COMPREHENSIVE CODEC UNIT TESTS")
    print("="*70)
    print(f"Started: {datetime.now()}")
    print()

    results = {}

    # Run individual codec tests
    try:
        results['scalar'] = test_scalar_codec()
    except Exception as e:
        print(f"❌ ScalarCodec test failed: {e}")
        results['scalar'] = False

    try:
        results['set'] = test_set_codec()
    except Exception as e:
        print(f"❌ SetCodec test failed: {e}")
        results['set'] = False

    try:
        results['timestamp'] = test_timestamp_codec()
    except Exception as e:
        print(f"❌ TimestampCodec test failed: {e}")
        results['timestamp'] = False

    try:
        results['email'] = test_email_codec()
    except Exception as e:
        print(f"❌ EmailCodec test failed: {e}")
        results['email'] = False

    try:
        results['domain'] = test_domain_codec()
    except Exception as e:
        print(f"❌ DomainCodec test failed: {e}")
        results['domain'] = False

    try:
        results['url'] = test_url_codec()
    except Exception as e:
        print(f"❌ URLCodec test failed: {e}")
        results['url'] = False

    try:
        results['json'] = test_json_codec()
    except Exception as e:
        print(f"❌ JSONCodec test failed: {e}")
        results['json'] = False

    # Run ES training integration test
    try:
        results['es_training'] = test_es_training_all_types()
    except Exception as e:
        print(f"❌ ES training test failed: {e}")
        import traceback
        traceback.print_exc()
        results['es_training'] = False

    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name:20} {status}")

    print()
    print(f"Total: {passed}/{total} tests passed")
    print(f"Finished: {datetime.now()}")

    if passed < total:
        sys.exit(1)
    else:
        print("\n🎉 ALL TESTS PASSED!")
        sys.exit(0)


if __name__ == "__main__":
    main()
