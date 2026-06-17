import pickle
import numpy as np

def load_model():
    with open("models/isolation_forest.pkl", "rb") as f:
        model = pickle.load(f)
    with open("models/scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
    return model, scaler

def predict_anomaly(invoice: dict, model, scaler) -> dict:
    features = [
        invoice.get("amount", 0),
        invoice.get("quantity", 1),
        invoice.get("unit_price", 0),
        invoice.get("payment_delay", 0)
    ]

    X = np.array(features).reshape(1, -1)
    X_scaled = scaler.transform(X)

    prediction = model.predict(X_scaled)[0]
    anomaly_score = model.decision_function(X_scaled)[0]

    # Convert to risk score 0-100
    # More negative score = more anomalous
    ml_risk_score = round((1 - (anomaly_score + 0.5)) * 100, 2)
    ml_risk_score = max(0, min(100, ml_risk_score))

    is_anomaly = True if prediction == -1 else False

    return {
        "is_anomaly": is_anomaly,
        "ml_risk_score": ml_risk_score
    }