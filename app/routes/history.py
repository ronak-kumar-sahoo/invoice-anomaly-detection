from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.crud import (
    get_all_records,
    get_anomalies_only,
    get_record_by_invoice_id,
    get_stats
)
import json

router = APIRouter()

@router.get("/history")
def get_history(db: Session = Depends(get_db)):
    records = get_all_records(db)
    return [
        {
            "invoice_id": r.invoice_id,
            "vendor_id": r.vendor_id,
            "category": r.category,
            "amount": r.amount,
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

@router.get("/history/anomalies")
def get_anomalies(db: Session = Depends(get_db)):
    records = get_anomalies_only(db)
    return [
        {
            "invoice_id": r.invoice_id,
            "vendor_id": r.vendor_id,
            "category": r.category,
            "amount": r.amount,
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

@router.get("/history/{invoice_id}")
def get_by_invoice_id(invoice_id: str, db: Session = Depends(get_db)):
    record = get_record_by_invoice_id(db, invoice_id)
    if not record:
        return {"error": f"Invoice {invoice_id} not found"}
    return {
        "invoice_id": record.invoice_id,
        "vendor_id": record.vendor_id,
        "category": record.category,
        "amount": record.amount,
        "is_anomaly": record.is_anomaly,
        "ml_risk_score": record.ml_risk_score,
        "rule_risk_score": record.rule_risk_score,
        "final_risk_score": record.final_risk_score,
        "risk_level": record.risk_level,
        "flags": json.loads(record.flags) if record.flags else [],
        "created_at": str(record.created_at)
    }

@router.get("/stats")
def get_statistics(db: Session = Depends(get_db)):
    return get_stats(db)