import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import pickle
import os

def load_data():
    df = pd.read_csv("data/raw/invoices.csv")
    print(f"Loaded {len(df)} records")
    return df

def preprocess(df):
    features = ["amount", "quantity", "unit_price", "payment_delay"]
    X = df[features].copy()
    y = df["is_anomaly"]

    # Split BEFORE fitting anything, so the test set is truly unseen.
    # Stratify on y since anomalies are only ~8% of the data.
    # Split on the full df (not just X) so we can persist the held-out
    # rows -- with all original columns (invoice_id, anomaly_type, etc.)
    # -- for invoice_evaluate.py to reuse the exact same test set later.
    train_df, test_df = train_test_split(
        df, test_size=0.2, random_state=42, stratify=y
    )

    X_train, X_test = train_df[features], test_df[features]
    y_train, y_test = train_df["is_anomaly"], test_df["is_anomaly"]

    # Fit the scaler on train only, then apply it to test
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    return X_train_scaled, X_test_scaled, y_train, y_test, scaler, features, test_df

def train_isolation_forest(X_scaled):
    print("\nTraining Isolation Forest...")
    model = IsolationForest(
        n_estimators=100,
        contamination=0.08,
        random_state=42
    )
    model.fit(X_scaled)
    print("Training complete.")
    return model

def evaluate(model, X_scaled, y):
    preds = model.predict(X_scaled)
    # Isolation Forest returns -1 for anomaly, 1 for normal
    # Convert to 1 for anomaly, 0 for normal
    preds_binary = [1 if p == -1 else 0 for p in preds]

    print("\nClassification Report:")
    print(classification_report(y, preds_binary, target_names=["Normal", "Anomaly"]))

    print("Confusion Matrix:")
    print(confusion_matrix(y, preds_binary))

    return preds_binary

def save_model(model, scaler):
    os.makedirs("models", exist_ok=True)
    with open("models/isolation_forest.pkl", "wb") as f:
        pickle.dump(model, f)
    with open("models/scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    print("\nModels saved to models/ folder")

if __name__ == "__main__":
    df = load_data()
    X_train_scaled, X_test_scaled, y_train, y_test, scaler, features, test_df = preprocess(df)

    model = train_isolation_forest(X_train_scaled)

    print("\n" + "=" * 50)
    print("HELD-OUT TEST SET RESULTS (honest numbers)")
    print("=" * 50)
    preds = evaluate(model, X_test_scaled, y_test)

    # Save the model trained on the train split + the scaler fit on train.
    # (We deliberately do NOT retrain on 100% of the data afterward --
    # doing so would silently reintroduce train/test contamination for
    # anyone who re-evaluates later using data/raw/invoices.csv.)
    save_model(model, scaler)

    # Persist the exact held-out test rows so invoice_evaluate.py can
    # reuse this same test set instead of re-evaluating on the full
    # (already-seen) training data.
    os.makedirs("data/processed", exist_ok=True)
    test_df.to_csv("data/processed/invoice_test.csv", index=False)
    print("Held-out test set saved to data/processed/invoice_test.csv")

    print("\nTraining pipeline complete.")