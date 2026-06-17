def apply_rules(invoice: dict) -> dict:
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

    return {
        "flags": flags,
        "rule_risk_score": min(risk_score, 100)
    }