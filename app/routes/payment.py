from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from app.schemas.payment import PaymentInput, PaymentResponse, PaymentUploadResponse
from app.models.payment_ml_model import load_payment_model, predict_payment_anomaly
from app.models.payment_rule_engine import apply_payment_rules
from app.database.db import get_db
from app.database.crud import (
    save_payment_result,
    get_all_payment_records,
    get_payment_anomalies_only,
    get_payment_stats
)
import json
import pandas as pd
import io

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

    save_payment_result(db, payment_dict, result)
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

        save_payment_result(db, payment_dict, result)
        results.append(result)

    return {
        "total_records": len(results),
        "anomalies_found": anomaly_count,
        "anomaly_percentage": round((anomaly_count / len(results)) * 100, 2),
        "results": results
    }

@router.get("/payment/history")
def payment_history(db: Session = Depends(get_db)):
    records = get_all_payment_records(db)
    return [
        {
            "payment_id": r.payment_id,
            "vendor_id": r.vendor_id,
            "invoice_amount": r.invoice_amount,
            "paid_amount": r.paid_amount,
            "payment_method": r.payment_method,
            "transaction_hour": r.transaction_hour,
            "is_anomaly": r.is_anomaly,
            "ml_risk_score": r.ml_risk_score,
            "rule_risk_score": r.rule_risk_score,
            "final_risk_score": r.final_risk_score,
            "risk_level": r.risk_level,
            "flags": json.loads(r.flags) if r.flags else [],
            "created_at": str(r.created_at)
        }
        for r in records
    ]

@router.get("/payment/history/anomalies")
def payment_anomalies(db: Session = Depends(get_db)):
    records = get_payment_anomalies_only(db)
    return [
        {
            "payment_id": r.payment_id,
            "vendor_id": r.vendor_id,
            "invoice_amount": r.invoice_amount,
            "paid_amount": r.paid_amount,
            "payment_method": r.payment_method,
            "transaction_hour": r.transaction_hour,
            "is_anomaly": r.is_anomaly,
            "final_risk_score": r.final_risk_score,
            "risk_level": r.risk_level,
            "flags": json.loads(r.flags) if r.flags else [],
            "created_at": str(r.created_at)
        }
        for r in records
    ]

@router.get("/payment/stats")
def payment_stats(db: Session = Depends(get_db)):
    return get_payment_stats(db)