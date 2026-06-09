from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from app.models.ml_model import load_model, predict_anomaly
from app.models.rule_engine import apply_rules
from app.database.db import get_db
from app.database.crud import save_invoice_result
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import re
import io
import uuid

router = APIRouter()

model, scaler = load_model()

# Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_image(image):
    text = pytesseract.image_to_string(image)
    return text

def extract_text_from_pdf(file_bytes):
    images = convert_from_bytes(file_bytes)
    text = ""
    for image in images:
        text += extract_text_from_image(image)
    return text

def parse_invoice_fields(text: str) -> dict:
    text_lower = text.lower()

    # Extract amount
    amount = 0.0
    amount_patterns = [
        r'total[:\s]+₹?\s*([\d,]+\.?\d*)',
        r'amount[:\s]+₹?\s*([\d,]+\.?\d*)',
        r'due[:\s]+₹?\s*([\d,]+\.?\d*)',
        r'invoice amount[:\s]+₹?\s*([\d,]+\.?\d*)',
        r'₹\s*([\d,]+\.?\d*)',
        r'\$\s*([\d,]+\.?\d*)'
    ]
    for pattern in amount_patterns:
        match = re.search(pattern, text_lower)
        if match:
            amount = float(match.group(1).replace(",", ""))
            break

    # Extract invoice ID
    invoice_id = f"INV-PDF-{str(uuid.uuid4())[:8].upper()}"
    id_patterns = [
        r'invoice\s*no[:\s]+([A-Z0-9\-]+)',
        r'invoice\s*number[:\s]+([A-Z0-9\-]+)',
        r'ref[:\s]+([A-Z0-9\-]+)',
        r'bill\s*no[:\s]+([A-Z0-9\-]+)'
    ]
    for pattern in id_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            invoice_id = match.group(1).strip()
            break

    # Extract vendor
    vendor_id = "VENDOR_UNKNOWN"
    vendor_patterns = [
        r'vendor[:\s]+([A-Za-z0-9\s]+)',
        r'supplier[:\s]+([A-Za-z0-9\s]+)',
        r'from[:\s]+([A-Za-z0-9\s]+)',
        r'billed by[:\s]+([A-Za-z0-9\s]+)'
    ]
    for pattern in vendor_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            vendor_id = match.group(1).strip()[:20]
            break

    # Extract payment delay
    payment_delay = 0
    delay_patterns = [
        r'net\s*(\d+)',
        r'payment\s*terms[:\s]+(\d+)\s*days',
        r'due\s*in\s*(\d+)\s*days',
        r'(\d+)\s*days'
    ]
    for pattern in delay_patterns:
        match = re.search(pattern, text_lower)
        if match:
            payment_delay = int(match.group(1))
            break

    # Extract quantity
    quantity = 1
    qty_patterns = [
        r'quantity[:\s]+(\d+)',
        r'qty[:\s]+(\d+)',
        r'units[:\s]+(\d+)'
    ]
    for pattern in qty_patterns:
        match = re.search(pattern, text_lower)
        if match:
            quantity = int(match.group(1))
            break

    unit_price = round(amount / quantity, 2) if quantity > 0 else amount

    return {
        "invoice_id": invoice_id,
        "vendor_id": vendor_id,
        "category": "General",
        "amount": amount,
        "quantity": quantity,
        "unit_price": unit_price,
        "payment_delay": payment_delay
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

@router.post("/predict/document")
async def predict_from_document(
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
            return {"error": f"Unsupported file type: {filename}. Send PDF, JPG or PNG only."}

        if not text or len(text.strip()) < 10:
            return {"error": "Could not extract text from document. Make sure it is a clear PDF or image."}

        # Parse fields from text
        invoice_dict = parse_invoice_fields(text)

        # Run through ML + rules
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
            "extracted_text": text[:500],
            "parsed_fields": invoice_dict,
            "message": f"Document analyzed. Risk level: {final['risk_level']}"
        }

        save_invoice_result(db, invoice_dict, result)
        return result

    except Exception as e:
        return {"error": f"Processing failed: {str(e)}"}