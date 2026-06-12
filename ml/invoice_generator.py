import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import timedelta
import os

fake = Faker()
random.seed(42)
np.random.seed(42)

VENDORS = [f"VENDOR_{i:03d}" for i in range(1, 51)]
CATEGORIES = ["Software", "Hardware", "Consulting", "Marketing", "Logistics", "Office Supplies"]

def generate_invoice_data(n_records=2000):
    invoices = []

    for i in range(n_records):
        vendor_id = random.choice(VENDORS)
        category = random.choice(CATEGORIES)
        issue_date = fake.date_between(start_date="-1y", end_date="today")
        due_date = issue_date + timedelta(days=random.choice([15, 30, 45, 60]))
        payment_date = due_date + timedelta(days=random.randint(-5, 10))
        amount = round(random.uniform(500, 50000), 2)
        quantity = random.randint(1, 100)
        unit_price = round(amount / quantity, 2)
        payment_delay = (payment_date - due_date).days
        is_anomaly = 0

        invoices.append({
            "invoice_id": f"INV-{i+1:05d}",
            "vendor_id": vendor_id,
            "category": category,
            "amount": amount,
            "quantity": quantity,
            "unit_price": unit_price,
            "issue_date": issue_date,
            "due_date": due_date,
            "payment_date": payment_date,
            "payment_delay": payment_delay,
            "is_anomaly": is_anomaly
        })

    return invoices

def inject_anomalies(invoices):
    n = len(invoices)
    anomaly_count = int(n * 0.08)  # 8% anomalies

    # Type 1 — Duplicate invoices
    for _ in range(anomaly_count // 4):
        original = random.choice(invoices)
        duplicate = original.copy()
        duplicate["invoice_id"] = f"INV-DUP-{fake.unique.random_int(10000, 99999)}"
        duplicate["is_anomaly"] = 1
        duplicate["anomaly_type"] = "duplicate"
        invoices.append(duplicate)

    # Type 2 — Round number fraud
    for _ in range(anomaly_count // 4):
        idx = random.randint(0, n - 1)
        invoices[idx]["amount"] = float(random.choice([5000, 10000, 25000, 50000, 100000]))
        invoices[idx]["is_anomaly"] = 1
        invoices[idx]["anomaly_type"] = "round_number"

    # Type 3 — Abnormal payment delay
    for _ in range(anomaly_count // 4):
        idx = random.randint(0, n - 1)
        invoices[idx]["payment_delay"] = random.choice([random.randint(90, 180), random.randint(-60, -30)])
        invoices[idx]["is_anomaly"] = 1
        invoices[idx]["anomaly_type"] = "payment_delay"

    # Type 4 — Vendor amount spike
    for _ in range(anomaly_count // 4):
        idx = random.randint(0, n - 1)
        invoices[idx]["amount"] = round(random.uniform(500000, 1000000), 2)
        invoices[idx]["is_anomaly"] = 1
        invoices[idx]["anomaly_type"] = "amount_spike"

    return invoices

def save_data(invoices):
    df = pd.DataFrame(invoices)
    df["anomaly_type"] = df.get("anomaly_type", "none")
    df["anomaly_type"] = df["anomaly_type"].fillna("none")

    os.makedirs("data/raw", exist_ok=True)
    df.to_csv("data/raw/invoices.csv", index=False)
    print(f"Dataset saved: {len(df)} records")
    print(f"Anomalies: {df['is_anomaly'].sum()} ({df['is_anomaly'].mean()*100:.1f}%)")
    print(f"Anomaly types:\n{df['anomaly_type'].value_counts()}")
    return df

if __name__ == "__main__":
    print("Generating invoice data...")
    invoices = generate_invoice_data(2000)
    invoices = inject_anomalies(invoices)
    df = save_data(invoices)
    print("\nSample data:")
    print(df.head())
    print("\nData shape:", df.shape)