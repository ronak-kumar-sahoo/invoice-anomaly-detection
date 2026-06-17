def apply_payment_rules(payment: dict) -> dict:
    flags = []
    risk_score = 0

    # Rule 1 — Late night transaction
    transaction_hour = payment.get("transaction_hour", 12)
    if 1 <= transaction_hour <= 4:
        flags.append("late_night_transaction")
        risk_score += 40

    # Rule 2 — Partial payment
    invoice_amount = payment.get("invoice_amount", 0)
    paid_amount = payment.get("paid_amount", 0)
    if invoice_amount > 0:
        payment_ratio = paid_amount / invoice_amount
        if payment_ratio < 0.9:
            flags.append("partial_payment")
            risk_score += 35
        elif payment_ratio > 1.1:
            flags.append("overpayment")
            risk_score += 30

    # Rule 3 — High frequency payments
    payment_frequency = payment.get("payment_frequency", 1)
    if payment_frequency >= 8:
        flags.append("high_frequency_payment")
        risk_score += 35

    # Rule 4 — Unusual payment method change
    payment_method = payment.get("payment_method", "")
    previous_method = payment.get("previous_method", "")
    if payment_method and previous_method:
        if payment_method != previous_method:
            if payment_method == "Cash" or previous_method == "Cash":
                flags.append("suspicious_method_change")
                risk_score += 40
            else:
                flags.append("payment_method_change")
                risk_score += 20

    # Rule 5 — Cash payment for large amount
    if payment_method == "Cash" and paid_amount > 10000:
        flags.append("large_cash_payment")
        risk_score += 45

    # Rule 6 — Zero or negative payment
    if paid_amount <= 0:
        flags.append("invalid_payment_amount")
        risk_score += 50

    return {
        "flags": flags,
        "rule_risk_score": min(risk_score, 100)
    }