#!/usr/bin/env python3
"""
Test ESTrainingDataTimeline class - simple mode.

Verifies that the timeline wrapper preserves existing ES training behavior.
"""
import sys
from pathlib import Path

# Paths
test_dir = Path(__file__).parent
neural_dir = test_dir.parent
featrix_dir = neural_dir.parent
lib_dir = featrix_dir.parent
src_dir = lib_dir.parent

sys.path.insert(0, str(lib_dir))
sys.path.insert(0, str(src_dir))

import pandas as pd
from featrix.neural.input_data_set import FeatrixInputDataSet
from featrix.neural.training_data_timeline import ESTrainingDataTimeline
from featrix.neural.gpu_utils import set_backend_cpu

set_backend_cpu()

print("=" * 80)
print("TEST: ESTrainingDataTimeline - Simple Mode")
print("=" * 80)

# Create simple test data
df = pd.DataFrame({
    'a': range(100),
    'b': [f'val_{i}' for i in range(100)],
    'c': [i * 1.5 for i in range(100)],
})

print(f"\n1. Creating FeatrixInputDataSet with {len(df)} rows...")
dataset = FeatrixInputDataSet(df=df, limit_rows=None)
print(f"   Dataset created: {len(dataset.df)} rows")

print("\n2. Splitting dataset (80/20)...")
train_ds, val_ds = dataset.split(fraction=0.2)
print(f"   Train: {len(train_ds.df)} rows")
print(f"   Val: {len(val_ds.df)} rows")

print("\n3. Creating ESTrainingDataTimeline from existing split...")
timeline = ESTrainingDataTimeline.from_existing_split(train_ds, val_ds)
print(f"   Timeline: {timeline}")
print(f"   is_chunked: {timeline.is_chunked}")
print(f"   train_row_count: {timeline.train_row_count}")
print(f"   epochs_per_pass: {timeline.epochs_per_pass}")

print("\n4. Verifying data access...")
# Warmup should be None in simple mode
warmup = timeline.get_warmup()
assert warmup is None, "Warmup should be None in simple mode"
print(f"   get_warmup(): None (correct)")

# Training data should be the same object
train_data = timeline.get_next_train_set(epoch_idx=0)
assert train_data is train_ds, "get_next_train_set should return same object in simple mode"
print(f"   get_next_train_set(0): Same as train_ds (correct)")

# Multiple epochs should return same data
train_data_2 = timeline.get_next_train_set(epoch_idx=5)
assert train_data_2 is train_ds, "get_next_train_set should return same object for any epoch"
print(f"   get_next_train_set(5): Same as train_ds (correct)")

# Validation should be the same object
val_data = timeline.get_validation_set()
assert val_data is val_ds, "get_validation_set should return same object"
print(f"   get_validation_set(): Same as val_ds (correct)")

# Test should be None
test_data = timeline.get_test_set()
assert test_data is None, "Test set should be None in simple mode"
print(f"   get_test_set(): None (correct)")

print("\n5. Testing direct access properties...")
assert timeline.train_input_data is train_ds
print(f"   timeline.train_input_data: Same as train_ds (correct)")
assert timeline.val_input_data is val_ds
print(f"   timeline.val_input_data: Same as val_ds (correct)")

print("\n6. Testing from_dataset factory...")
timeline2 = ESTrainingDataTimeline.from_dataset(dataset, val_fraction=0.2)
print(f"   Timeline: {timeline2}")
print(f"   train_row_count: {timeline2.train_row_count}")

print("\n" + "=" * 80)
print("✅ All tests passed!")
print("=" * 80)
