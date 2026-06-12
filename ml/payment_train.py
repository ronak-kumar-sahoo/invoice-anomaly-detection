import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
import pickle
import os

def load_data():
    df = pd.read_csv("data/raw/payments.csv")
    print(f"Loaded {len(df)} payment records")
    return df

def preprocess(df):
    # Encode payment method
    le = LabelEncoder()
    df["payment_method_encoded"] = le.fit_transform(df["payment_method"])
    df["previous_method_encoded"] = le.fit_transform(df["previous_method"])

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

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return X_scaled, y, scaler, features, le

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

def save_model(model, scaler, le):
    os.makedirs("models", exist_ok=True)
    with open("models/payment_isolation_forest.pkl", "wb") as f:
        pickle.dump(model, f)
    with open("models/payment_scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    with open("models/payment_label_encoder.pkl", "wb") as f:
        pickle.dump(le, f)
    print("\nPayment models saved to models/ folder")

if __name__ == "__main__":
    df = load_data()
    X_scaled, y, scaler, features, le = preprocess(df)
    model = train_payment_model(X_scaled)
    evaluate(model, X_scaled, y)
    save_model(model, scaler, le)
    print("\nPayment training pipeline complete.")