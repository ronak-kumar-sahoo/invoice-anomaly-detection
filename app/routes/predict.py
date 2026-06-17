from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.invoice import InvoiceInput, AnomalyResponse
from app.models.invoice_ml_model import load_model, predict_anomaly
from app.models.invoice_rule_engine import apply_rules
from app.database.db import get_db
from app.database.crud import save_invoice_result

router = APIRouter()

model, scaler = load_model()

def calculate_final_score(ml_score: float, rule_score: float) -> dict:
    # 60% ML score + 40% rule score
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

@router.post("/predict", response_model=AnomalyResponse)
def predict(invoice: InvoiceInput, db: Session = Depends(get_db)):
    invoice_dict = invoice.dict()

    # ML prediction
    ml_result = predict_anomaly(invoice_dict, model, scaler)

    # Rule based prediction
    rule_result = apply_rules(invoice_dict)

    # Combine scores
    final = calculate_final_score(
        ml_result["ml_risk_score"],
        rule_result["rule_risk_score"]
    )

    result = {
    "invoice_id": str(invoice_dict["invoice_id"]),
    "vendor_id": str(invoice_dict["vendor_id"]),
    "amount": float(invoice_dict["amount"]),
    "is_anomaly": bool(ml_result["is_anomaly"]),
    "ml_risk_score": float(ml_result["ml_risk_score"]),
    "rule_risk_score": float(rule_result["rule_risk_score"]),
    "final_risk_score": float(final["final_risk_score"]),
    "risk_level": str(final["risk_level"]),
    "flags": list(rule_result["flags"]),
    "message": f"Invoice analyzed. Risk level: {str(final['risk_level'])}"
}

    # Save to database
    save_invoice_result(db, invoice_dict, result)

    return result