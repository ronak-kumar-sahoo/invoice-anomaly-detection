import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
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

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return X_scaled, y, scaler, features

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
    X_scaled, y, scaler, features = preprocess(df)
    model = train_isolation_forest(X_scaled)
    preds = evaluate(model, X_scaled, y)
    save_model(model, scaler)
    print("\nTraining pipeline complete.")