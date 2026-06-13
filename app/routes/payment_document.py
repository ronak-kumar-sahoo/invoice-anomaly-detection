from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from app.models.payment_ml_model import load_payment_model, predict_payment_anomaly
from app.models.payment_rule_engine import apply_payment_rules
from app.database.db import get_db
from app.database.crud import save_payment_result
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import re
import io
import uuid

router = APIRouter()

model, scaler, le = load_payment_model()

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_image(image):
    return pytesseract.image_to_string(image)

def extract_text_from_pdf(file_bytes):
    images = convert_from_bytes(file_bytes)
    text = ""
    for image in images:
        text += extract_text_from_image(image)
    return text

def calculate_confidence(fields: dict) -> int:
    total_fields = 6
    found = 0
    if fields["paid_amount"] > 0: found += 1
    if fields["payment_method"] != "NEFT": found += 1
    if fields["transaction_hour"] != 10: found += 1
    if fields["payment_id"] != "auto_generated": found += 1
    if fields["vendor_id"] != "VENDOR_UNKNOWN": found += 1
    if fields["payment_frequency"] != 1: found += 1
    return round((found / total_fields) * 100)
def parse_payment_fields(text: str) -> dict:
    text_lower = text.lower()

    # Extract paid amount
    paid_amount = 0.0
    amount_patterns = [
        r'₹\s*([\d,]+\.?\d*)',
        r'rs\.?\s*([\d,]+\.?\d*)',
        r'inr\s*([\d,]+\.?\d*)',
        r'amount[:\s]+[^\d]{0,3}([\d,]+\.?\d*)',
        r'paid[:\s]+[^\d]{0,3}([\d,]+\.?\d*)',
        r'[^\d]([\d]{1,3}(?:,\d{2,3})+(?:\.\d{1,2})?)\b',  # fallback: any number like 4,600 or 1,000
    ]
    for pattern in amount_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            amt_str = m.replace(",", "")
            try:
                amt = float(amt_str)
                if amt > 0:
                    paid_amount = amt
                    break
            except:
                continue
        if paid_amount > 0:
            break
        
    # Extract payment/transaction ID
    payment_id = "auto_generated"
    id_patterns = [
        r'utr[:\s]*(\d+)',
        r'transaction\s*id[:\s]*([A-Za-z0-9]+)',
        r'upi\s*ref\s*no[:\s.]*([0-9]+)',
        r'ref\s*no[:\s.]*([0-9]+)',
        r'txn\s*id[:\s]*([A-Za-z0-9]+)',
    ]
    for pattern in id_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            payment_id = match.group(1).strip()
            break
    if payment_id == "auto_generated":
        payment_id = f"PAY-DOC-{str(uuid.uuid4())[:8].upper()}"

    # Extract vendor / counterparty name
    vendor_id = "VENDOR_UNKNOWN"
    vendor_patterns = [
        r'to\n([A-Za-z\s]+)',
        r'to[:\s]+([A-Za-z][A-Za-z\s]{2,30})',
        r'received from\n?([A-Za-z\s]+)',
        r'from[:\s]+([A-Za-z][A-Za-z\s]{2,30})',
        r'beneficiary[:\s]+([A-Za-z][A-Za-z\s]{2,30})',
        r'payee[:\s]+([A-Za-z][A-Za-z\s]{2,30})',
    ]
    for pattern in vendor_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            # remove trailing newlines / extra words
            candidate = candidate.split("\n")[0].strip()
            if len(candidate) > 2:
                vendor_id = candidate[:30]
                break

    # Extract payment method (generic detection)
    payment_method = "UPI"
    if "rtgs" in text_lower:
        payment_method = "RTGS"
    elif "neft" in text_lower:
        payment_method = "NEFT"
    elif "cheque" in text_lower or "check no" in text_lower:
        payment_method = "Cheque"
    elif "cash" in text_lower and "cashback" not in text_lower:
        payment_method = "Cash"
    elif "upi" in text_lower or "@" in text_lower or "vpa" in text_lower:
        payment_method = "UPI"
    else:
        payment_method = "UPI"  # default for digital transaction screenshots

    # Extract transaction hour
    transaction_hour = 12
    time_patterns = [
        r'paid at\s+(\d{1,2}):(\d{2})\s*(am|pm)',
        r'at\s+(\d{1,2}):(\d{2})\s*(am|pm)',
        r'(\d{1,2}):(\d{2})\s*(am|pm)',
        r'(\d{1,2}):(\d{2})\s+on',
    ]
    for pattern in time_patterns:
        match = re.search(pattern, text_lower)
        if match:
            hour = int(match.group(1))
            groups = match.groups()
            if len(groups) >= 3 and groups[2]:
                if groups[2] == "pm" and hour != 12:
                    hour += 12
                elif groups[2] == "am" and hour == 12:
                    hour = 0
            transaction_hour = hour
            break

    return {
        "payment_id": payment_id,
        "vendor_id": vendor_id,
        "invoice_amount": paid_amount,
        "paid_amount": paid_amount,
        "payment_method": payment_method,
        "previous_method": payment_method,
        "transaction_hour": transaction_hour,
        "payment_frequency": 1,
        "is_partial_payment": False
    }

def calculate_final_score(ml_score: float, rule_score: float) -> dict:
    final_score = round((ml_score * 0.6) + (rule_score * 0.4), 2)
    if final_score >= 70:
        risk_level = "HIGH"
    elif final_score >= 40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    return {"final_risk_score": final_score, "risk_level": risk_level}

@router.post("/payment/document")
async def predict_payment_from_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    contents = await file.read()
    filename = file.filename.lower().strip()

    try:
        # Extract text based on file type
        if filename.endswith(".pdf"):
            text = extract_text_from_pdf(contents)
        elif filename.endswith((".jpg", ".jpeg", ".png")):
            image = Image.open(io.BytesIO(contents))
            text = extract_text_from_image(image)
        else:
            return {"error": f"Unsupported file type. Send PDF, JPG or PNG only."}

        if not text or len(text.strip()) < 10:
            return {"error": "Could not extract text. Make sure document is clear."}

        # Parse payment fields
        payment_dict = parse_payment_fields(text)

        # Calculate confidence
        confidence = calculate_confidence(payment_dict)

        # Run through ML + rules
        ml_result = predict_payment_anomaly(payment_dict, model, scaler, le)
        rule_result = apply_payment_rules(payment_dict)
        final = calculate_final_score(
            ml_result["ml_risk_score"],
            rule_result["rule_risk_score"]
        )
        save_payment_result(db, payment_dict, {
                    "is_anomaly": ml_result["is_anomaly"],
                    "ml_risk_score": ml_result["ml_risk_score"],
                    "rule_risk_score": rule_result["rule_risk_score"],
                    "final_risk_score": final["final_risk_score"],
                    "risk_level": final["risk_level"],
                    "flags": rule_result["flags"]
                })
        return {
            "payment_id": payment_dict["payment_id"],
            "vendor_id": payment_dict["vendor_id"],
            "paid_amount": payment_dict["paid_amount"],
            "payment_method": payment_dict["payment_method"],
            "transaction_hour": payment_dict["transaction_hour"],
            "is_anomaly": ml_result["is_anomaly"],
            "ml_risk_score": ml_result["ml_risk_score"],
            "rule_risk_score": rule_result["rule_risk_score"],
            "final_risk_score": final["final_risk_score"],
            "risk_level": final["risk_level"],
            "flags": rule_result["flags"],
            "confidence_score": confidence,
            "extracted_text": text[:500],
            "parsed_fields": payment_dict,
            "message": f"Payment document analyzed. Risk: {final['risk_level']} | Confidence: {confidence}%"
        }

    except Exception as e:
        return {"error": f"Processing failed: {str(e)}"}