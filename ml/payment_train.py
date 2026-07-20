import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import pickle
import os

def load_data():
    df = pd.read_csv("data/raw/payments.csv")
    print(f"Loaded {len(df)} payment records")
    return df

def preprocess(df):
    # Two SEPARATE encoders -- reusing one LabelEncoder for both columns
    # meant the second .fit_transform() silently overwrote the first
    # encoder's learned classes, corrupting payment_method_encoded at
    # inference time.
    le_payment_method = LabelEncoder()
    le_previous_method = LabelEncoder()
    df["payment_method_encoded"] = le_payment_method.fit_transform(df["payment_method"])
    df["previous_method_encoded"] = le_previous_method.fit_transform(df["previous_method"])

    features = [
        "paid_amount",
        "transaction_hour",
        "payment_frequency",
        "is_partial_payment",
        "payment_method_encoded",
        "previous_method_encoded"
    ]

    X = df[features].copy()
    X["is_partial_payment"] = X["is_partial_payment"].astype(int)
    y = df["is_anomaly"]

    # Split BEFORE fitting the scaler, so the test set is truly unseen.
    # Split on the full df (not just X) so we can persist the held-out
    # rows -- with all original columns (payment_id, anomaly_type, etc.)
    # -- for payment_evaluate.py to reuse the exact same test set later.
    train_df, test_df = train_test_split(
        df, test_size=0.2, random_state=42, stratify=y
    )
    X_train, X_test = train_df[features].copy(), test_df[features].copy()
    X_train["is_partial_payment"] = X_train["is_partial_payment"].astype(int)
    X_test["is_partial_payment"] = X_test["is_partial_payment"].astype(int)
    y_train, y_test = train_df["is_anomaly"], test_df["is_anomaly"]

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    return X_train_scaled, X_test_scaled, y_train, y_test, scaler, features, le_payment_method, le_previous_method, test_df

def train_payment_model(X_scaled):
    print("\nTraining Payment Isolation Forest...")
    model = IsolationForest(
        n_estimators=100,
        contamination=0.08,
        random_state=123
    )
    model.fit(X_scaled)
    print("Training complete.")
    return model

def evaluate(model, X_scaled, y):
    preds = model.predict(X_scaled)
    preds_binary = [1 if p == -1 else 0 for p in preds]

    print("\nPayment Model Classification Report:")
    print(classification_report(y, preds_binary,
          target_names=["Normal", "Anomaly"]))

    print("Confusion Matrix:")
    print(confusion_matrix(y, preds_binary))

    return preds_binary

def save_model(model, scaler, le_payment_method, le_previous_method):
    os.makedirs("models", exist_ok=True)
    with open("models/payment_isolation_forest.pkl", "wb") as f:
        pickle.dump(model, f)
    with open("models/payment_scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    with open("models/payment_method_label_encoder.pkl", "wb") as f:
        pickle.dump(le_payment_method, f)
    with open("models/previous_method_label_encoder.pkl", "wb") as f:
        pickle.dump(le_previous_method, f)
    print("\nPayment models saved to models/ folder")

if __name__ == "__main__":
    df = load_data()
    (X_train_scaled, X_test_scaled, y_train, y_test, scaler,
     features, le_payment_method, le_previous_method, test_df) = preprocess(df)

    model = train_payment_model(X_train_scaled)

    print("\n" + "=" * 50)
    print("HELD-OUT TEST SET RESULTS (honest numbers)")
    print("=" * 50)
    evaluate(model, X_test_scaled, y_test)

    save_model(model, scaler, le_payment_method, le_previous_method)

    # Persist the exact held-out test rows so payment_evaluate.py can
    # reuse this same test set instead of re-evaluating on training data.
    os.makedirs("data/processed", exist_ok=True)
    test_df.to_csv("data/processed/payment_test.csv", index=False)
    print("Held-out test set saved to data/processed/payment_test.csv")

    print("\nPayment training pipeline complete.")