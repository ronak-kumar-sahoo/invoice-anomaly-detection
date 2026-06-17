import pickle
import numpy as np

def load_payment_model():
    with open("models/payment_isolation_forest.pkl", "rb") as f:
        model = pickle.load(f)
    with open("models/payment_scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
    with open("models/payment_label_encoder.pkl", "rb") as f:
        le = pickle.load(f)
    return model, scaler, le

def predict_payment_anomaly(payment: dict, model, scaler, le) -> dict:
    try:
        payment_method_encoded = le.transform([payment.get("payment_method", "NEFT")])[0]
        previous_method_encoded = le.transform([payment.get("previous_method", "NEFT")])[0]
    except:
        payment_method_encoded = 0
        previous_method_encoded = 0

    features = [
        payment.get("paid_amount", 0),
        payment.get("transaction_hour", 12),
        payment.get("payment_frequency", 1),
        int(payment.get("is_partial_payment", False)),
        payment_method_encoded,
        previous_method_encoded
    ]

    X = np.array(features).reshape(1, -1)
    X_scaled = scaler.transform(X)

    prediction = model.predict(X_scaled)[0]
    anomaly_score = model.decision_function(X_scaled)[0]

    ml_risk_score = round((1 - (anomaly_score + 0.5)) * 100, 2)
    ml_risk_score = max(0, min(100, ml_risk_score))

    is_anomaly = True if prediction == -1 else False

    return {
        "is_anomaly": is_anomaly,
        "ml_risk_score": ml_risk_score
    }