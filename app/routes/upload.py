from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from app.models.ml_model import load_model, predict_anomaly
from app.models.rule_engine import apply_rules
from app.database.db import get_db
from app.database.crud import save_invoice_result
from app.schemas.invoice import UploadResponse
import pandas as pd
import io

router = APIRouter()

model, scaler = load_model()

def calculate_final_score(ml_score: float, rule_score: float) -> dict:
    final_score = round((ml_score * 0.6) + (rule_score * 0.4), 2)

    if final_score >= 70:
        risk_level = "HIGH"
    elif final_score >= 40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "final_risk_score": final_score,
        "risk_level": risk_level
    }

@router.post("/upload", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))

    required_columns = ["invoice_id", "vendor_id", "category",
                        "amount", "quantity", "unit_price", "payment_delay"]

    for col in required_columns:
        if col not in df.columns:
            return {"error": f"Missing column: {col}"}

    results = []
    anomaly_count = 0

    for _, row in df.iterrows():
        invoice_dict = {
            "invoice_id": str(row["invoice_id"]),
            "vendor_id": str(row["vendor_id"]),
            "category": str(row["category"]),
            "amount": float(row["amount"]),
            "quantity": int(row["quantity"]),
            "unit_price": float(row["unit_price"]),
            "payment_delay": int(row["payment_delay"])
        }

        ml_result = predict_anomaly(invoice_dict, model, scaler)
        rule_result = apply_rules(invoice_dict)
        final = calculate_final_score(
            ml_result["ml_risk_score"],
            rule_result["rule_risk_score"]
        )

        result = {
            "invoice_id": invoice_dict["invoice_id"],
            "vendor_id": invoice_dict["vendor_id"],
            "amount": invoice_dict["amount"],
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

        save_invoice_result(db, invoice_dict, result)
        results.append(result)

    return {
        "total_records": len(results),
        "anomalies_found": anomaly_count,
        "anomaly_percentage": round((anomaly_count / len(results)) * 100, 2),
        "results": results
    }