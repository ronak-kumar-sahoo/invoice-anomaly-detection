from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from app.schemas.payment import PaymentInput, PaymentResponse, PaymentUploadResponse
from app.models.payment_ml_model import load_payment_model, predict_payment_anomaly
from app.models.payment_rule_engine import apply_payment_rules
from app.database.db import get_db
import pandas as pd
import io
import json

router = APIRouter()

model, scaler, le = load_payment_model()

def calculate_final_score(ml_score: float, rule_score: float) -> dict:
    final_score = round((ml_score * 0.6) + (rule_score * 0.4), 2)
    if final_score >= 70:
        risk_level = "HIGH"
    elif final_score >= 40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    return {"final_risk_score": final_score, "risk_level": risk_level}

@router.post("/payment/predict", response_model=PaymentResponse)
def predict_payment(payment: PaymentInput, db: Session = Depends(get_db)):
    payment_dict = payment.dict()

    ml_result = predict_payment_anomaly(payment_dict, model, scaler, le)
    rule_result = apply_payment_rules(payment_dict)
    final = calculate_final_score(
        ml_result["ml_risk_score"],
        rule_result["rule_risk_score"]
    )

    result = {
        "payment_id": payment_dict["payment_id"],
        "vendor_id": payment_dict["vendor_id"],
        "paid_amount": payment_dict["paid_amount"],
        "is_anomaly": ml_result["is_anomaly"],
        "ml_risk_score": ml_result["ml_risk_score"],
        "rule_risk_score": rule_result["rule_risk_score"],
        "final_risk_score": final["final_risk_score"],
        "risk_level": final["risk_level"],
        "flags": rule_result["flags"],
        "message": f"Payment analyzed. Risk level: {final['risk_level']}"
    }

    return result

@router.post("/payment/upload", response_model=PaymentUploadResponse)
async def upload_payment_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))

    required_columns = [
        "payment_id", "vendor_id", "invoice_amount",
        "paid_amount", "payment_method", "previous_method",
        "transaction_hour", "payment_frequency", "is_partial_payment"
    ]

    for col in required_columns:
        if col not in df.columns:
            return {"error": f"Missing column: {col}"}

    results = []
    anomaly_count = 0

    for _, row in df.iterrows():
        payment_dict = {
            "payment_id": str(row["payment_id"]),
            "vendor_id": str(row["vendor_id"]),
            "invoice_amount": float(row["invoice_amount"]),
            "paid_amount": float(row["paid_amount"]),
            "payment_method": str(row["payment_method"]),
            "previous_method": str(row["previous_method"]),
            "transaction_hour": int(row["transaction_hour"]),
            "payment_frequency": int(row["payment_frequency"]),
            "is_partial_payment": bool(row["is_partial_payment"])
        }

        ml_result = predict_payment_anomaly(payment_dict, model, scaler, le)
        rule_result = apply_payment_rules(payment_dict)
        final = calculate_final_score(
            ml_result["ml_risk_score"],
            rule_result["rule_risk_score"]
        )

        result = {
            "payment_id": payment_dict["payment_id"],
            "vendor_id": payment_dict["vendor_id"],
            "paid_amount": payment_dict["paid_amount"],
            "is_anomaly": ml_result["is_anomaly"],
            "ml_risk_score": ml_result["ml_risk_score"],
            "rule_risk_score": rule_result["rule_risk_score"],
            "final_risk_score": final["final_risk_score"],
            "risk_level": final["risk_level"],
            "flags": rule_result["flags"],
            "message": f"Risk level: {final['risk_level']}"
        }

        if ml_result["is_anomaly"]:
            anomaly_count += 1

        results.append(result)

    return {
        "total_records": len(results),
        "anomalies_found": anomaly_count,
        "anomaly_percentage": round((anomaly_count / len(results)) * 100, 2),
        "results": results
    }

@router.get("/payment/history")
def get_payment_history():
    return {"message": "Payment history endpoint ready"}

@router.get("/payment/stats")
def get_payment_stats():
    return {"message": "Payment stats endpoint ready"}