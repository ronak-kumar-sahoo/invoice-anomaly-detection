from sqlalchemy.orm import Session
from app.database.db import InvoiceRecord
import json

def save_invoice_result(db: Session, invoice_data: dict, result: dict):
    record = InvoiceRecord(
    invoice_id=str(invoice_data.get("invoice_id")),
    vendor_id=str(invoice_data.get("vendor_id")),
    category=str(invoice_data.get("category")),
    amount=float(invoice_data.get("amount")),
    quantity=int(invoice_data.get("quantity")),
    unit_price=float(invoice_data.get("unit_price")),
    payment_delay=int(invoice_data.get("payment_delay")),
    is_anomaly=bool(result.get("is_anomaly")),
    ml_risk_score=float(result.get("ml_risk_score")),
    rule_risk_score=float(result.get("rule_risk_score")),
    final_risk_score=float(result.get("final_risk_score")),
    risk_level=str(result.get("risk_level")),
    flags=json.dumps(result.get("flags", []))
)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_all_records(db: Session, limit: int = 100):
    return db.query(InvoiceRecord).order_by(
        InvoiceRecord.created_at.desc()
    ).limit(limit).all()

def get_anomalies_only(db: Session, limit: int = 100):
    return db.query(InvoiceRecord).filter(
        InvoiceRecord.is_anomaly == True
    ).order_by(
        InvoiceRecord.created_at.desc()
    ).limit(limit).all()

def get_record_by_invoice_id(db: Session, invoice_id: str):
    return db.query(InvoiceRecord).filter(
        InvoiceRecord.invoice_id == invoice_id
    ).first()

def get_stats(db: Session):
    total = db.query(InvoiceRecord).count()
    anomalies = db.query(InvoiceRecord).filter(
        InvoiceRecord.is_anomaly == True
    ).count()
    return {
        "total_records": total,
        "total_anomalies": anomalies,
        "anomaly_percentage": round((anomalies / total * 100), 2) if total > 0 else 0
    }
from app.database.db import PaymentRecord

def save_payment_result(db: Session, payment_data: dict, result: dict):
    record = PaymentRecord(
    payment_id=str(payment_data.get("payment_id")),
    vendor_id=str(payment_data.get("vendor_id")),
    invoice_amount=float(payment_data.get("invoice_amount")),
    paid_amount=float(payment_data.get("paid_amount")),
    payment_method=str(payment_data.get("payment_method")),
    previous_method=str(payment_data.get("previous_method")),
    transaction_hour=int(payment_data.get("transaction_hour")),
    payment_frequency=int(payment_data.get("payment_frequency")),
    is_partial_payment=bool(payment_data.get("is_partial_payment")),
    is_anomaly=bool(result.get("is_anomaly")),
    ml_risk_score=float(result.get("ml_risk_score")),
    rule_risk_score=float(result.get("rule_risk_score")),
    final_risk_score=float(result.get("final_risk_score")),
    risk_level=str(result.get("risk_level")),
    flags=json.dumps(result.get("flags", []))
)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_all_payment_records(db: Session, limit: int = 100):
    return db.query(PaymentRecord).order_by(
        PaymentRecord.created_at.desc()
    ).limit(limit).all()

def get_payment_anomalies_only(db: Session, limit: int = 100):
    return db.query(PaymentRecord).filter(
        PaymentRecord.is_anomaly == True
    ).order_by(
        PaymentRecord.created_at.desc()
    ).limit(limit).all()

def get_payment_stats(db: Session):
    total = db.query(PaymentRecord).count()
    anomalies = db.query(PaymentRecord).filter(
        PaymentRecord.is_anomaly == True
    ).count()
    return {
        "total_records": total,
        "total_anomalies": anomalies,
        "anomaly_percentage": round((anomalies / total * 100), 2) if total > 0 else 0
    }