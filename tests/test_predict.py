import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✅ Health check passed")

def test_root():
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    assert "version" in response.json()
    print("✅ Root endpoint passed")

def test_predict_normal_invoice():
    payload = {
        "invoice_id": "TEST-001",
        "vendor_id": "VENDOR_012",
        "category": "Software",
        "amount": 15420.50,
        "quantity": 10,
        "unit_price": 1542.05,
        "payment_delay": 5
    }
    response = requests.post(f"{BASE_URL}/predict", json=payload)
    assert response.status_code == 200
    result = response.json()
    assert "risk_level" in result
    assert "final_risk_score" in result
    assert result["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    print(f"✅ Normal invoice test passed → Risk: {result['risk_level']}")

def test_predict_high_risk_invoice():
    payload = {
        "invoice_id": "TEST-002",
        "vendor_id": "VENDOR_001",
        "category": "Consulting",
        "amount": 1000000.00,
        "quantity": 10,
        "unit_price": 100000.00,
        "payment_delay": 150
    }
    response = requests.post(f"{BASE_URL}/predict", json=payload)
    assert response.status_code == 200
    result = response.json()
    assert result["risk_level"] == "HIGH"
    assert result["is_anomaly"] == True
    print(f"✅ High risk invoice test passed → Risk: {result['risk_level']}")

def test_predict_missing_field():
    payload = {
        "invoice_id": "TEST-003",
        "vendor_id": "VENDOR_012"
        # missing required fields
    }
    response = requests.post(f"{BASE_URL}/predict", json=payload)
    assert response.status_code == 422
    print("✅ Missing field validation test passed")

def test_stats():
    response = requests.get(f"{BASE_URL}/stats")
    assert response.status_code == 200
    result = response.json()
    assert "total_records" in result
    assert "total_anomalies" in result
    print(f"✅ Stats test passed → Total records: {result['total_records']}")

def test_history():
    response = requests.get(f"{BASE_URL}/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    print(f"✅ History test passed → {len(response.json())} records found")

def test_payment_predict_normal():
    payload = {
        "payment_id": "PAY-TEST-001",
        "vendor_id": "VENDOR_012",
        "invoice_amount": 15420.50,
        "paid_amount": 15420.50,
        "payment_method": "NEFT",
        "previous_method": "NEFT",
        "transaction_hour": 14,
        "payment_frequency": 2,
        "is_partial_payment": False
    }
    response = requests.post(f"{BASE_URL}/payment/predict", json=payload)
    assert response.status_code == 200
    result = response.json()
    assert "risk_level" in result
    assert result["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    print(f"✅ Normal payment test passed → Risk: {result['risk_level']}")

def test_payment_predict_high_risk():
    payload = {
        "payment_id": "PAY-TEST-002",
        "vendor_id": "VENDOR_001",
        "invoice_amount": 50000.00,
        "paid_amount": 25000.00,
        "payment_method": "Cash",
        "previous_method": "NEFT",
        "transaction_hour": 2,
        "payment_frequency": 12,
        "is_partial_payment": True
    }
    response = requests.post(f"{BASE_URL}/payment/predict", json=payload)
    assert response.status_code == 200
    result = response.json()
    assert result["risk_level"] == "HIGH"
    print(f"✅ High risk payment test passed → Risk: {result['risk_level']}")

def test_payment_stats():
    response = requests.get(f"{BASE_URL}/payment/stats")
    assert response.status_code == 200
    result = response.json()
    assert "total_records" in result
    assert "total_anomalies" in result
    print(f"✅ Payment stats test passed → Total records: {result['total_records']}")

def test_payment_history():
    response = requests.get(f"{BASE_URL}/payment/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    print(f"✅ Payment history test passed → {len(response.json())} records found")

if __name__ == "__main__":
    print("=" * 50)
    print("RUNNING API TESTS")
    print("=" * 50)
    print("Make sure FastAPI server is running on port 8000")
    print("=" * 50 + "\n")

    try:
        test_health()
        test_root()
        test_predict_normal_invoice()
        test_predict_high_risk_invoice()
        test_predict_missing_field()
        test_stats()
        test_history()
        test_payment_predict_normal()
        test_payment_predict_high_risk()
        test_payment_stats()
        test_payment_history()

        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED")
        print("=" * 50)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("Make sure FastAPI server is running first.")