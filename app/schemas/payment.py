from pydantic import BaseModel
from typing import Optional

class PaymentInput(BaseModel):
    payment_id: str
    vendor_id: str
    invoice_amount: float
    paid_amount: float
    payment_method: str
    previous_method: str
    transaction_hour: int
    payment_frequency: int
    is_partial_payment: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "payment_id": "PAY-00001",
                "vendor_id": "VENDOR_012",
                "invoice_amount": 15420.50,
                "paid_amount": 15420.50,
                "payment_method": "NEFT",
                "previous_method": "NEFT",
                "transaction_hour": 14,
                "payment_frequency": 2,
                "is_partial_payment": False
            }
        }

class PaymentResponse(BaseModel):
    payment_id: str
    vendor_id: str
    paid_amount: float
    is_anomaly: bool
    ml_risk_score: float
    rule_risk_score: float
    final_risk_score: float
    risk_level: str
    flags: list
    message: str

class PaymentUploadResponse(BaseModel):
    total_records: int
    anomalies_found: int
    anomaly_percentage: float
    results: list