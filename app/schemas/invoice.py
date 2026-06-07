from pydantic import BaseModel
from typing import Optional

class InvoiceInput(BaseModel):
    invoice_id: str
    vendor_id: str
    category: str
    amount: float
    quantity: int
    unit_price: float
    payment_delay: int

    class Config:
        json_schema_extra = {
            "example": {
                "invoice_id": "INV-00001",
                "vendor_id": "VENDOR_012",
                "category": "Software",
                "amount": 15420.50,
                "quantity": 10,
                "unit_price": 1542.05,
                "payment_delay": 5
            }
        }

class AnomalyResponse(BaseModel):
    invoice_id: str
    vendor_id: str
    amount: float
    is_anomaly: bool
    ml_risk_score: float
    rule_risk_score: float
    final_risk_score: float
    risk_level: str
    flags: list
    message: str

class UploadResponse(BaseModel):
    total_records: int
    anomalies_found: int
    anomaly_percentage: float
    results: list