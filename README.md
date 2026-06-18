# Invoice & Payment Anomaly Detection System

An end-to-end API-based system for detecting anomalies in invoices and payment transactions using Machine Learning and rule-based logic.

---

## Project Overview

This system detects fraudulent and suspicious invoices and payments using a two-layer detection approach:
- **ML Layer** — Isolation Forest models trained on invoice and payment patterns
- **Rule Layer** — Business logic rules for domain-specific fraud detection

Both layers combine into a final risk score with three levels — LOW, MEDIUM, HIGH.

---

## Features

### Invoice Anomaly Detection
- Single invoice analysis via REST API
- Bulk CSV invoice processing
- PDF and Image invoice processing with OCR
- Real-time risk scoring

### Payment Anomaly Detection
- Single payment analysis via REST API
- Bulk CSV payment processing
- Payment receipt/screenshot upload (UPI, NEFT, RTGS, Cheque) with OCR
- Confidence scoring for document extraction
- Real-time risk scoring

### General
- Interactive dashboard with separate Invoice and Payment modules
- SQLite database for storing results
- Swagger UI for API documentation and testing
- Automated API tests

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI |
| ML Model | Scikit-learn (Isolation Forest) |
| OCR | Tesseract + Poppler |
| Database | SQLite / PostgreSQL |
| Dashboard | Streamlit |
| Data Processing | Pandas, NumPy |
| Visualization | Plotly, Matplotlib |

---

## Project Structure

```
invoice-anomaly-detection/
├── app/
│   ├── database/
│   │   ├── crud.py
│   │   └── db.py
│   ├── models/
│   │   ├── invoice_ml_model.py
│   │   ├── invoice_rule_engine.py
│   │   ├── payment_ml_model.py
│   │   └── payment_rule_engine.py
│   ├── routes/
│   │   ├── predict.py
│   │   ├── upload.py
│   │   ├── history.py
│   │   ├── pdf_upload.py
│   │   ├── payment.py
│   │   └── payment_document.py
│   ├── schemas/
│   │   ├── invoice.py
│   │   └── payment.py
│   └── main.py
├── ml/
│   ├── invoice_generator.py
│   ├── invoice_train.py
│   ├── invoice_evaluate.py
│   ├── payment_generator.py
│   └── payment_train.py
├── dashboard/
│   └── app.py
├── tests/
│   └── test_predict.py
├── requirements.txt
└── README.md
```

---

## Anomaly Types Detected

### Invoice Anomalies

| Type | Description |
|---|---|
| Duplicate Invoice | Same vendor, same amount, close dates |
| Round Number Fraud | Suspiciously round amounts |
| Payment Delay | Unusually late or early payments |
| Amount Spike | Vendor invoicing abnormally large amounts |
| Quantity Mismatch | Quantity x unit price does not match total |
| Invalid Amount | Zero or negative invoice amounts |

### Payment Anomalies

| Type | Description |
|---|---|
| Late Night Transaction | Payment made between 1 AM - 4 AM |
| Partial Payment | Paid amount significantly less than invoice amount |
| Overpayment | Paid amount significantly more than invoice amount |
| High Frequency Payment | Vendor paid 8+ times in a month |
| Suspicious Method Change | Payment method changed involving Cash |
| Large Cash Payment | Cash payment above ₹10,000 |
| Invalid Payment Amount | Zero or negative paid amount |

---

## API Endpoints

### Invoice Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | / | Root endpoint |
| GET | /health | Health check |
| POST | /predict | Single invoice prediction |
| POST | /upload | Bulk CSV upload |
| POST | /predict/document | PDF or Image upload |
| GET | /history | All analyzed invoices |
| GET | /history/anomalies | Anomalies only |
| GET | /history/{invoice_id} | Single invoice lookup |
| GET | /stats | System statistics |

### Payment Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /payment/predict | Single payment prediction |
| POST | /payment/upload | Bulk CSV upload |
| POST | /payment/document | Payment receipt/screenshot upload |
| GET | /payment/history | All analyzed payments |
| GET | /payment/history/anomalies | Payment anomalies only |
| GET | /payment/stats | Payment statistics |

---

## Model Performance

- Algorithm: Isolation Forest
- Contamination rate: 8%
- Evaluation metrics: Precision, Recall, F1, ROC AUC
- Separate models trained for invoice and payment anomalies

---

## Installation and Setup

### 1. Clone the repository
```bash
git clone https://github.com/ronakbhatt/invoice-anomaly-detection.git
cd invoice-anomaly-detection
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Tesseract OCR
Download from: https://github.com/UB-Mannheim/tesseract/wiki

### 5. Install Poppler
Download from: https://github.com/oschwartz10612/poppler-windows/releases

### 6. Generate data and train models
```bash
python ml/invoice_generator.py
python ml/invoice_train.py
python ml/payment_generator.py
python ml/payment_train.py
```

### 7. Start the API
```bash
uvicorn app.main:app --reload
```

### 8. Start the dashboard
```bash
streamlit run dashboard/app.py
```

---

## Usage

### API Documentation
Visit: http://127.0.0.1:8000/docs

### Dashboard
Visit: http://localhost:8501

### Run Tests
```bash
python tests/test_predict.py
```

---

## Input Format

### JSON Single Invoice
```json
{
  "invoice_id": "INV-00001",
  "vendor_id": "VENDOR_012",
  "category": "Software",
  "amount": 15420.50,
  "quantity": 10,
  "unit_price": 1542.05,
  "payment_delay": 5
}
```

### JSON Single Payment
```json
{
  "payment_id": "PAY-00001",
  "vendor_id": "VENDOR_012",
  "invoice_amount": 15420.50,
  "paid_amount": 15420.50,
  "payment_method": "NEFT",
  "previous_method": "NEFT",
  "transaction_hour": 14,
  "payment_frequency": 2,
  "is_partial_payment": false
}
```

### Document Upload
Supported formats: PDF, JPG, JPEG, PNG
- Invoice documents: extracts invoice fields automatically
- Payment receipts/screenshots: extracts amount, vendor, transaction ID, payment method

---

## Risk Levels

| Score | Risk Level | Action |
|---|---|---|
| 0 - 39 | LOW | Normal transaction |
| 40 - 69 | MEDIUM | Review recommended |
| 70 - 100 | HIGH | Immediate investigation |

---

## Future Improvements

- Switch to PostgreSQL for production
- Add authentication and API keys
- Train on real invoice and payment datasets
- Add email alerts for HIGH risk transactions
- Deploy on cloud (Render + Streamlit Cloud)
- Real-time pre-payment fraud detection via payment gateway webhooks

---

## Author

**Ronak**
- [text](https://github.com/ronak-kumar-sahoo)

## Live Demo

- **Swagger UI:** https://invoice-anomaly-detection-1.onrender.com/docs
- **Streamlit Dashboard:** https://invoice-anomaly-detection-4ryyjggxbjzllukcrtxjvx.streamlit.app/
