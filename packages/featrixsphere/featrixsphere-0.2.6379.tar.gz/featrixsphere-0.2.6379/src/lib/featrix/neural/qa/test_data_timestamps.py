#!/usr/bin/env python3
"""
Generate test dataset with timestamp columns for testing temporal relationship ops.

Creates a synthetic dataset with:
- 2 timestamp columns (order_date, ship_date) - for timestamp×timestamp relationships
- 3 string columns (customer_name, product_category, status) - for string×timestamp relationships
- 2 numeric columns (amount, quantity) - standard scalar columns
- 1 target column (is_late) - binary classification target

The ship_date is typically 1-7 days after order_date, with "late" shipments taking longer.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_timestamps_dataset(n_rows: int = 500, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic dataset with timestamp columns."""
    np.random.seed(seed)
    random.seed(seed)

    # Customer names
    first_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

    # Product categories
    categories = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books", "Toys", "Food", "Health"]

    # Status values
    statuses = ["Delivered", "In Transit", "Processing", "Shipped", "Pending"]

    # Day names for some string columns that should correlate with timestamps
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    data = []
    base_date = datetime(2024, 1, 1)

    for i in range(n_rows):
        # Generate order date (random day in 2024)
        order_offset = random.randint(0, 364)
        order_date = base_date + timedelta(days=order_offset)

        # Generate shipping delay (1-10 days, with some correlation to "late" status)
        is_late = random.random() < 0.3  # 30% late
        if is_late:
            ship_delay = random.randint(5, 14)  # Late shipments: 5-14 days
        else:
            ship_delay = random.randint(1, 4)   # Normal shipments: 1-4 days

        ship_date = order_date + timedelta(days=ship_delay)

        # Add some hour variation
        order_date = order_date.replace(
            hour=random.randint(8, 20),
            minute=random.randint(0, 59)
        )
        ship_date = ship_date.replace(
            hour=random.randint(6, 18),
            minute=random.randint(0, 59)
        )

        # Generate other fields
        customer_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        category = random.choice(categories)

        # Status correlates with lateness
        if is_late:
            status = random.choice(["In Transit", "Processing", "Pending"])
        else:
            status = random.choice(["Delivered", "Shipped"])

        # Order day name (should correlate with order_date)
        order_day = day_names[order_date.weekday()]

        # Amount and quantity
        amount = round(random.uniform(10, 500), 2)
        quantity = random.randint(1, 10)

        data.append({
            "order_date": order_date,
            "ship_date": ship_date,
            "customer_name": customer_name,
            "product_category": category,
            "status": status,
            "order_day": order_day,  # String that should correlate with order_date's day of week
            "amount": amount,
            "quantity": quantity,
            "is_late": int(is_late),
        })

    df = pd.DataFrame(data)
    return df


def main():
    """Generate and save the test dataset."""
    import os

    # Generate dataset
    df = generate_timestamps_dataset(n_rows=500)

    # Save to CSV
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, "timestamps_test_data.csv")
    df.to_csv(output_path, index=False)

    print(f"Generated dataset with {len(df)} rows")
    print(f"Saved to: {output_path}")
    print(f"\nColumns:")
    for col in df.columns:
        print(f"  - {col}: {df[col].dtype}")
    print(f"\nSample rows:")
    print(df.head(3).to_string())
    print(f"\nTarget distribution:")
    print(df["is_late"].value_counts())


if __name__ == "__main__":
    main()
