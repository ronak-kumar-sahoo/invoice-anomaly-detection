import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import timedelta, datetime
import os

fake = Faker()
random.seed(123)
np.random.seed(123)

VENDORS = [f"VENDOR_{i:03d}" for i in range(1, 51)]
PAYMENT_METHODS = ["UPI", "NEFT", "RTGS", "Cheque", "Cash"]

def generate_payment_data(n_records=2000):
    payments = []

    for i in range(n_records):
        vendor_id = random.choice(VENDORS)
        payment_method = random.choice(PAYMENT_METHODS)
        paid_amount = round(random.uniform(500, 50000), 2)
        transaction_hour = random.randint(9, 18)
        payment_date = fake.date_between(start_date="-1y", end_date="today")
        payment_frequency = random.randint(1, 4)
        is_partial_payment = False
        invoice_amount = paid_amount
        previous_method = payment_method

        payments.append({
            "payment_id": f"PAY-{i+1:05d}",
            "vendor_id": vendor_id,
            "invoice_amount": invoice_amount,
            "paid_amount": paid_amount,
            "payment_method": payment_method,
            "previous_method": previous_method,
            "transaction_hour": transaction_hour,
            "payment_date": str(payment_date),
            "payment_frequency": payment_frequency,
            "is_partial_payment": is_partial_payment,
            "is_anomaly": 0,
            "anomaly_type": "none"
        })

    return payments

def inject_payment_anomalies(payments):
    n = len(payments)
    anomaly_count = int(n * 0.08)

    # Type 1 — Late night transaction
    for _ in range(anomaly_count // 5):
        idx = random.randint(0, n - 1)
        payments[idx]["transaction_hour"] = random.randint(1, 4)
        payments[idx]["is_anomaly"] = 1
        payments[idx]["anomaly_type"] = "late_night_transaction"

    # Type 2 — Partial payment
    for _ in range(anomaly_count // 5):
        idx = random.randint(0, n - 1)
        payments[idx]["paid_amount"] = round(
            payments[idx]["invoice_amount"] * random.uniform(0.5, 0.8), 2
        )
        payments[idx]["is_partial_payment"] = True
        payments[idx]["is_anomaly"] = 1
        payments[idx]["anomaly_type"] = "partial_payment"

    # Type 3 — High frequency payments
    for _ in range(anomaly_count // 5):
        idx = random.randint(0, n - 1)
        payments[idx]["payment_frequency"] = random.randint(8, 15)
        payments[idx]["is_anomaly"] = 1
        payments[idx]["anomaly_type"] = "high_frequency"

    # Type 4 — Unusual payment method change
    for _ in range(anomaly_count // 5):
        idx = random.randint(0, n - 1)
        current = payments[idx]["payment_method"]
        different = random.choice([m for m in PAYMENT_METHODS if m != current])
        payments[idx]["previous_method"] = current
        payments[idx]["payment_method"] = different
        payments[idx]["is_anomaly"] = 1
        payments[idx]["anomaly_type"] = "method_change"

    # Type 5 — Overpayment
    for _ in range(anomaly_count // 5):
        idx = random.randint(0, n - 1)
        payments[idx]["paid_amount"] = round(
            payments[idx]["invoice_amount"] * random.uniform(1.2, 2.0), 2
        )
        payments[idx]["is_anomaly"] = 1
        payments[idx]["anomaly_type"] = "overpayment"

    return payments

def save_payment_data(payments):
    df = pd.DataFrame(payments)
    df["anomaly_type"] = df["anomaly_type"].fillna("none")

    os.makedirs("data/raw", exist_ok=True)
    df.to_csv("data/raw/payments.csv", index=False)
    print(f"Payment dataset saved: {len(df)} records")
    print(f"Anomalies: {df['is_anomaly'].sum()} ({df['is_anomaly'].mean()*100:.1f}%)")
    print(f"Anomaly types:\n{df['anomaly_type'].value_counts()}")
    return df

if __name__ == "__main__":
    print("Generating payment data...")
    payments = generate_payment_data(2000)
    payments = inject_payment_anomalies(payments)
    df = save_payment_data(payments)
    print("\nSample data:")
    print(df.head())
    print("\nData shape:", df.shape)