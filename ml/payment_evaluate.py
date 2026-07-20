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
    with open("models/payment_isolation_forest.pkl", "rb") as f:
        model = pickle.load(f)
    with open("models/payment_scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
    with open("models/payment_method_label_encoder.pkl", "rb") as f:
        le_payment_method = pickle.load(f)
    with open("models/previous_method_label_encoder.pkl", "rb") as f:
        le_previous_method = pickle.load(f)
    return model, scaler, le_payment_method, le_previous_method

def load_data(le_payment_method, le_previous_method):
    # Evaluate on the held-out test set saved by payment_train.py --
    # NOT the raw training file. Scoring on data/raw/payments.csv here
    # would silently re-introduce train/test contamination.
    test_path = "data/processed/payment_test.csv"
    if not os.path.exists(test_path):
        raise FileNotFoundError(
            f"{test_path} not found. Run `python ml/payment_train.py` first "
            "to generate the held-out test set before evaluating."
        )
    df = pd.read_csv(test_path)

    df["payment_method_encoded"] = le_payment_method.transform(df["payment_method"])
    df["previous_method_encoded"] = le_previous_method.transform(df["previous_method"])

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
    return X, y, df

def evaluate_model(model, scaler, X, y):
    X_scaled = scaler.transform(X)

    preds = model.predict(X_scaled)
    preds_binary = [1 if p == -1 else 0 for p in preds]

    scores = model.decision_function(X_scaled)
    scores_normalized = [round((1 - (s + 0.5)) * 100, 2) for s in scores]
    scores_normalized = [max(0, min(100, s)) for s in scores_normalized]

    print("=" * 50)
    print("PAYMENT MODEL EVALUATION REPORT")
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

    try:
        auc = roc_auc_score(y, scores_normalized)
        print(f"\nROC AUC Score: {auc:.4f}")
    except Exception:
        print("\nROC AUC Score: Could not calculate")

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
        print(f"{atype:24s} -> Detected: {detected}/{total} ({rate}%)")

def save_evaluation_plots(y, scores_normalized):
    os.makedirs("data/processed", exist_ok=True)

    precision, recall, _ = precision_recall_curve(y, scores_normalized)
    plt.figure(figsize=(8, 6))
    plt.plot(recall, precision, marker='.', color='blue')
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Payment Model — Precision-Recall Curve")
    plt.grid(True)
    plt.savefig("data/processed/payment_precision_recall_curve.png")
    plt.close()
    print("\nPrecision-Recall curve saved to data/processed/payment_precision_recall_curve.png")

if __name__ == "__main__":
    print("Loading payment model and data...")
    model, scaler, le_payment_method, le_previous_method = load_artifacts()
    X, y, df = load_data(le_payment_method, le_previous_method)

    preds_binary, scores_normalized = evaluate_model(model, scaler, X, y)
    evaluate_by_anomaly_type(df, preds_binary)
    save_evaluation_plots(y, scores_normalized)

    print("\n" + "=" * 50)
    print("Payment evaluation complete.")
    print("=" * 50)