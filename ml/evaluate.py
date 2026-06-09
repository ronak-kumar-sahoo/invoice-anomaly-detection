import pandas as pd
import numpy as np
import pickle
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    precision_recall_curve,
    average_precision_score
)
import matplotlib.pyplot as plt
import os

def load_artifacts():
    with open("models/isolation_forest.pkl", "rb") as f:
        model = pickle.load(f)
    with open("models/scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
    return model, scaler

def load_data():
    df = pd.read_csv("data/raw/invoices.csv")
    features = ["amount", "quantity", "unit_price", "payment_delay"]
    X = df[features].copy()
    y = df["is_anomaly"]
    return X, y, df

def evaluate_model(model, scaler, X, y):
    X_scaled = scaler.transform(X)

    # Predictions
    preds = model.predict(X_scaled)
    preds_binary = [1 if p == -1 else 0 for p in preds]

    # Anomaly scores
    scores = model.decision_function(X_scaled)
    scores_normalized = [round((1 - (s + 0.5)) * 100, 2) for s in scores]
    scores_normalized = [max(0, min(100, s)) for s in scores_normalized]

    print("=" * 50)
    print("MODEL EVALUATION REPORT")
    print("=" * 50)

    print("\nClassification Report:")
    print(classification_report(y, preds_binary,
          target_names=["Normal", "Anomaly"]))

    print("Confusion Matrix:")
    cm = confusion_matrix(y, preds_binary)
    print(cm)
    print(f"\nTrue Negatives  (Normal correctly identified): {cm[0][0]}")
    print(f"False Positives (Normal wrongly flagged):       {cm[0][1]}")
    print(f"False Negatives (Anomaly missed):               {cm[1][0]}")
    print(f"True Positives  (Anomaly correctly caught):     {cm[1][1]}")

    # ROC AUC
    try:
        auc = roc_auc_score(y, scores_normalized)
        print(f"\nROC AUC Score: {auc:.4f}")
    except:
        print("\nROC AUC Score: Could not calculate")

    # Average precision
    ap = average_precision_score(y, scores_normalized)
    print(f"Average Precision Score: {ap:.4f}")

    return preds_binary, scores_normalized

def evaluate_by_anomaly_type(df, preds_binary):
    df = df.copy()
    df["predicted_anomaly"] = preds_binary

    print("\n" + "=" * 50)
    print("DETECTION RATE BY ANOMALY TYPE")
    print("=" * 50)

    anomaly_types = df[df["is_anomaly"] == 1]["anomaly_type"].unique()

    for atype in anomaly_types:
        if atype == "none":
            continue
        subset = df[df["anomaly_type"] == atype]
        detected = subset["predicted_anomaly"].sum()
        total = len(subset)
        rate = round(detected / total * 100, 1)
        print(f"{atype:20s} → Detected: {detected}/{total} ({rate}%)")

def save_evaluation_plots(y, scores_normalized):
    os.makedirs("data/processed", exist_ok=True)

    # Precision Recall Curve
    precision, recall, _ = precision_recall_curve(y, scores_normalized)
    plt.figure(figsize=(8, 6))
    plt.plot(recall, precision, marker='.', color='blue')
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall Curve")
    plt.grid(True)
    plt.savefig("data/processed/precision_recall_curve.png")
    plt.close()
    print("\nPrecision-Recall curve saved to data/processed/")

if __name__ == "__main__":
    print("Loading model and data...")
    model, scaler = load_artifacts()
    X, y, df = load_data()

    preds_binary, scores_normalized = evaluate_model(model, scaler, X, y)
    evaluate_by_anomaly_type(df, preds_binary)
    save_evaluation_plots(y, scores_normalized)

    print("\n" + "=" * 50)
    print("Evaluation complete.")
    print("=" * 50)