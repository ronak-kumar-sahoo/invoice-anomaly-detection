def apply_rules(invoice: dict, db=None) -> dict:
    flags = []
    risk_score = 0

    # Rule 1 — Round number fraud
    amount = invoice.get("amount", 0)
    if amount % 1000 == 0 and amount >= 5000:
        flags.append("round_number_amount")
        risk_score += 25

    # Rule 2 — Abnormal payment delay
    payment_delay = invoice.get("payment_delay", 0)
    if payment_delay > 60:
        flags.append("high_payment_delay")
        risk_score += 30
    elif payment_delay < -30:
        flags.append("unusually_early_payment")
        risk_score += 20

    # Rule 3 — Amount spike
    if amount > 500000:
        flags.append("amount_spike")
        risk_score += 40

    # Rule 4 — Zero or negative amount
    if amount <= 0:
        flags.append("invalid_amount")
        risk_score += 50

    # Rule 5 — Quantity mismatch
    quantity = invoice.get("quantity", 1)
    unit_price = invoice.get("unit_price", 0)
    expected_amount = round(quantity * unit_price, 2)
    if abs(expected_amount - amount) > 10:
        flags.append("quantity_amount_mismatch")
        risk_score += 35

    # Rule 6 — Duplicate invoice
    # Isolation Forest can't catch this: a duplicate has IDENTICAL
    # amount/quantity/unit_price/payment_delay to a real invoice, so it
    # isn't an outlier in feature space at all. This has to be an exact-
    # match lookup against previously seen invoices instead.
    if db is not None:
        from app.database.db import InvoiceRecord
        vendor_id = invoice.get("vendor_id")
        existing = db.query(InvoiceRecord).filter(
            InvoiceRecord.vendor_id == vendor_id,
            InvoiceRecord.amount == amount,
            InvoiceRecord.invoice_id != invoice.get("invoice_id")
        ).first()
        if existing is not None:
            flags.append("possible_duplicate")
            risk_score += 40

    return {
        "flags": flags,
        "rule_risk_score": min(risk_score, 100)
    }