import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import json
import os

API_URL = os.getenv(
    "API_URL",
    "https://invoice-anomaly-detection-1.onrender.com"
)

st.set_page_config(
    page_title="Invoice Anomaly Detection",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Invoice & Payment Anomaly Detection System")
st.markdown("---")

# Sidebar
st.sidebar.title("Invoice Analysis")
invoice_page = st.sidebar.radio("Invoice Module", [
    "Single Invoice Check",
    "Document Upload (PDF/Image)",
    "Bulk CSV Upload",
    "History & Analytics"
], key="invoice_nav")

st.sidebar.markdown("---")
st.sidebar.title("Payment Analysis")
payment_page = st.sidebar.radio("Payment Module", [
    "None",
    "Single Payment Check",
    "Payment Document Upload",
    "Bulk Payment CSV Upload",
    "Payment History & Analytics"
], key="payment_nav")

if payment_page != "None":
    page = payment_page
else:
    page = invoice_page

# ─── Page 1: Single Invoice Check ───
if page == "Single Invoice Check":
    st.header("Single Invoice Check")
    st.markdown("Fill in the invoice details below to check for anomalies.")

    col1, col2 = st.columns(2)

    with col1:
        invoice_id = st.text_input("Invoice ID", value="INV-00001")
        vendor_id = st.text_input("Vendor ID", value="VENDOR_012")
        category = st.selectbox("Category", [
            "Software", "Hardware", "Consulting",
            "Marketing", "Logistics", "Office Supplies"
        ])
        amount = st.number_input("Amount (₹)", min_value=0.0, value=15420.50)

    with col2:
        quantity = st.number_input("Quantity", min_value=1, value=10)
        unit_price = st.number_input("Unit Price (₹)", min_value=0.0, value=1542.05)
        payment_delay = st.number_input("Payment Delay (days)", value=5)

    if st.button("Analyze Invoice", type="primary"):
        payload = {
            "invoice_id": invoice_id,
            "vendor_id": vendor_id,
            "category": category,
            "amount": amount,
            "quantity": int(quantity),
            "unit_price": unit_price,
            "payment_delay": int(payment_delay)
        }

        with st.spinner("Analyzing..."):
            try:
                response = requests.post(f"{API_URL}/predict", json=payload)
                result = response.json()

                st.markdown("---")
                st.subheader("Analysis Result")

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("ML Risk Score", f"{result['ml_risk_score']:.1f}")
                col2.metric("Rule Risk Score", f"{result['rule_risk_score']:.1f}")
                col3.metric("Final Risk Score", f"{result['final_risk_score']:.1f}")

                risk = result["risk_level"]
                if risk == "HIGH":
                    col4.error(f"Risk Level: {risk}")
                elif risk == "MEDIUM":
                    col4.warning(f"Risk Level: {risk}")
                else:
                    col4.success(f"Risk Level: {risk}")

                if result["flags"]:
                    st.subheader("Anomaly Flags")
                    for flag in result["flags"]:
                        st.warning(f"⚠️ {flag.replace('_', ' ').title()}")
                else:
                    st.success("✅ No rule-based flags detected")

            except Exception as e:
                st.error(f"API Error: {e}")

# ─── Page 2: Document Upload ───
elif page == "Document Upload (PDF/Image)":
    st.header("Document Upload (PDF/Image)")
    st.markdown("Upload a PDF or image invoice for automatic extraction and anomaly detection.")

    uploaded_file = st.file_uploader(
        "Choose a PDF or Image file",
        type=["pdf", "jpg", "jpeg", "png"]
    )

    if uploaded_file and st.button("Analyze Document", type="primary"):
        with st.spinner("Extracting and analyzing document..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                response = requests.post(f"{API_URL}/predict/document", files=files)
                result = response.json()

                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    st.markdown("---")
                    st.subheader("Extracted Fields")
                    parsed = result.get("parsed_fields", {})
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"Invoice ID: {parsed.get('invoice_id', 'N/A')}")
                        st.info(f"Vendor: {parsed.get('vendor_id', 'N/A')}")
                        st.info(f"Amount: ₹{parsed.get('amount', 0)}")
                    with col2:
                        st.info(f"Quantity: {parsed.get('quantity', 0)}")
                        st.info(f"Payment Delay: {parsed.get('payment_delay', 0)} days")
                        st.info(f"Category: {parsed.get('category', 'N/A')}")

                    st.markdown("---")
                    st.subheader("Analysis Result")
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("ML Risk Score", f"{result['ml_risk_score']:.1f}")
                    col2.metric("Rule Risk Score", f"{result['rule_risk_score']:.1f}")
                    col3.metric("Final Risk Score", f"{result['final_risk_score']:.1f}")

                    risk = result["risk_level"]
                    if risk == "HIGH":
                        col4.error(f"Risk Level: {risk}")
                    elif risk == "MEDIUM":
                        col4.warning(f"Risk Level: {risk}")
                    else:
                        col4.success(f"Risk Level: {risk}")

                    if result["flags"]:
                        st.subheader("Anomaly Flags")
                        for flag in result["flags"]:
                            st.warning(f"⚠️ {flag.replace('_', ' ').title()}")
                    else:
                        st.success("✅ No rule-based flags detected")

                    with st.expander("See Extracted Text"):
                        st.text(result.get("extracted_text", ""))

            except Exception as e:
                st.error(f"Error: {e}")            

# ─── Page 3: Bulk CSV Upload ───
elif page == "Bulk CSV Upload":
    st.header("Bulk CSV Upload")
    st.markdown("Upload a CSV file to analyze multiple invoices at once.")

    st.info("CSV must have columns: invoice_id, vendor_id, category, amount, quantity, unit_price, payment_delay")

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file and st.button("Analyze CSV", type="primary"):
        with st.spinner("Analyzing all invoices..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file, "text/csv")}
                response = requests.post(f"{API_URL}/upload", files=files)
                result = response.json()

                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Records", result["total_records"])
                col2.metric("Anomalies Found", result["anomalies_found"])
                col3.metric("Anomaly %", f"{result['anomaly_percentage']}%")

                df = pd.DataFrame(result["results"])

                # Risk level distribution chart
                st.subheader("Risk Level Distribution")
                risk_counts = df["risk_level"].value_counts().reset_index()
                risk_counts.columns = ["Risk Level", "Count"]
                fig = px.bar(risk_counts, x="Risk Level", y="Count",
                             color="Risk Level",
                             color_discrete_map={
                                 "HIGH": "red",
                                 "MEDIUM": "orange",
                                 "LOW": "green"
                             })
                st.plotly_chart(fig, use_container_width=True)

                # Results table
                st.subheader("Detailed Results")
                st.dataframe(
                    df[["invoice_id", "vendor_id", "amount",
                        "final_risk_score", "risk_level", "is_anomaly"]],
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"API Error: {e}")
                
# ─── Payment Page 1: Single Payment Check ───
elif page == "Single Payment Check":
    st.header("Single Payment Check")
    st.markdown("Enter payment details to check for anomalies.")

    col1, col2 = st.columns(2)

    with col1:
        payment_id = st.text_input("Payment ID", value="PAY-00001")
        vendor_id = st.text_input("Vendor ID", value="VENDOR_012")
        invoice_amount = st.number_input("Invoice Amount (₹)", min_value=0.0, value=15420.50)
        paid_amount = st.number_input("Paid Amount (₹)", min_value=0.0, value=15420.50)

    with col2:
        payment_method = st.selectbox("Payment Method", ["UPI", "NEFT", "RTGS", "Cheque", "Cash"])
        previous_method = st.selectbox("Previous Payment Method", ["UPI", "NEFT", "RTGS", "Cheque", "Cash"])
        transaction_hour = st.slider("Transaction Hour (24h)", 0, 23, 14)
        payment_frequency = st.number_input("Payment Frequency (per month)", min_value=1, value=2)

    is_partial = st.checkbox("Is Partial Payment")

    if st.button("Analyze Payment", type="primary"):
        payload = {
            "payment_id": payment_id,
            "vendor_id": vendor_id,
            "invoice_amount": invoice_amount,
            "paid_amount": paid_amount,
            "payment_method": payment_method,
            "previous_method": previous_method,
            "transaction_hour": int(transaction_hour),
            "payment_frequency": int(payment_frequency),
            "is_partial_payment": is_partial
        }

        with st.spinner("Analyzing payment..."):
            try:
                response = requests.post(f"{API_URL}/payment/predict", json=payload)
                result = response.json()

                st.markdown("---")
                st.subheader("Analysis Result")

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("ML Risk Score", f"{result['ml_risk_score']:.1f}")
                col2.metric("Rule Risk Score", f"{result['rule_risk_score']:.1f}")
                col3.metric("Final Risk Score", f"{result['final_risk_score']:.1f}")

                risk = result["risk_level"]
                if risk == "HIGH":
                    col4.error(f"Risk Level: {risk}")
                elif risk == "MEDIUM":
                    col4.warning(f"Risk Level: {risk}")
                else:
                    col4.success(f"Risk Level: {risk}")

                if result["flags"]:
                    st.subheader("Anomaly Flags")
                    for flag in result["flags"]:
                        st.warning(f"⚠️ {flag.replace('_', ' ').title()}")
                else:
                    st.success("✅ No rule-based flags detected")

            except Exception as e:
                st.error(f"API Error: {e}")

# ─── Payment Page 2: Payment Document Upload ───
elif page == "Payment Document Upload":
    st.header("Payment Document Upload")
    st.markdown("Upload a payment receipt, UPI screenshot, bank transfer receipt, or cheque image.")

    st.info("Supported: UPI/NEFT/RTGS receipts, bank statements, cheque images (PDF, JPG, PNG)")

    uploaded_file = st.file_uploader(
        "Choose a payment document",
        type=["pdf", "jpg", "jpeg", "png"],
        key="payment_doc"
    )

    if uploaded_file and st.button("Analyze Payment Document", type="primary"):
        with st.spinner("Extracting and analyzing payment document..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                response = requests.post(f"{API_URL}/payment/document", files=files)
                result = response.json()

                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    confidence = result.get("confidence_score", 0)
                    st.markdown("---")
                    st.subheader("Extraction Confidence")
                    st.progress(confidence / 100)
                    st.write(f"Confidence: {confidence}%")

                    if confidence < 70:
                        st.warning("⚠️ Low confidence extraction. Please verify the fields below.")

                    parsed = result.get("parsed_fields", {})
                    st.subheader("Extracted Fields")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"Payment ID: {parsed.get('payment_id', 'N/A')}")
                        st.info(f"Vendor: {parsed.get('vendor_id', 'N/A')}")
                        st.info(f"Amount: ₹{parsed.get('paid_amount', 0)}")
                    with col2:
                        st.info(f"Method: {parsed.get('payment_method', 'N/A')}")
                        st.info(f"Transaction Hour: {parsed.get('transaction_hour', 0)}:00")

                    st.markdown("---")
                    st.subheader("Analysis Result")
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("ML Risk Score", f"{result['ml_risk_score']:.1f}")
                    col2.metric("Rule Risk Score", f"{result['rule_risk_score']:.1f}")
                    col3.metric("Final Risk Score", f"{result['final_risk_score']:.1f}")

                    risk = result["risk_level"]
                    if risk == "HIGH":
                        col4.error(f"Risk Level: {risk}")
                    elif risk == "MEDIUM":
                        col4.warning(f"Risk Level: {risk}")
                    else:
                        col4.success(f"Risk Level: {risk}")

                    if result["flags"]:
                        st.subheader("Anomaly Flags")
                        for flag in result["flags"]:
                            st.warning(f"⚠️ {flag.replace('_', ' ').title()}")
                    else:
                        st.success("✅ No rule-based flags detected")

                    with st.expander("See Extracted Text"):
                        st.text(result.get("extracted_text", ""))

            except Exception as e:
                st.error(f"Error: {e}")

# ─── Payment Page 3: Bulk Payment CSV Upload ───
elif page == "Bulk Payment CSV Upload":
    st.header("Bulk Payment CSV Upload")
    st.markdown("Upload a CSV file with payment records to analyze in bulk.")

    st.info("CSV must have columns: payment_id, vendor_id, invoice_amount, paid_amount, payment_method, previous_method, transaction_hour, payment_frequency, is_partial_payment")

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv", key="payment_csv")

    if uploaded_file and st.button("Analyze Payment CSV", type="primary"):
        with st.spinner("Analyzing all payments..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file, "text/csv")}
                response = requests.post(f"{API_URL}/payment/upload", files=files)
                result = response.json()

                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Records", result["total_records"])
                col2.metric("Anomalies Found", result["anomalies_found"])
                col3.metric("Anomaly %", f"{result['anomaly_percentage']}%")

                df = pd.DataFrame(result["results"])

                st.subheader("Risk Level Distribution")
                risk_counts = df["risk_level"].value_counts().reset_index()
                risk_counts.columns = ["Risk Level", "Count"]
                fig = px.bar(risk_counts, x="Risk Level", y="Count",
                             color="Risk Level",
                             color_discrete_map={
                                 "HIGH": "red",
                                 "MEDIUM": "orange",
                                 "LOW": "green"
                             })
                st.plotly_chart(fig, use_container_width=True)

                st.subheader("Detailed Results")
                st.dataframe(
                    df[["payment_id", "vendor_id", "paid_amount",
                        "final_risk_score", "risk_level", "is_anomaly"]],
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"API Error: {e}")

# ─── Page 4: History & Analytics ───
elif page == "History & Analytics":
    st.header("History & Analytics")

    try:
        # Stats
        stats = requests.get(f"{API_URL}/stats").json()
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Invoices", stats["total_records"])
        col2.metric("Total Anomalies", stats["total_anomalies"])
        col3.metric("Anomaly Rate", f"{stats['anomaly_percentage']}%")

        st.markdown("---")

        # History data
        history = requests.get(f"{API_URL}/history").json()

        if history:
            df = pd.DataFrame(history)

            # Risk score distribution
            st.subheader("Risk Score Distribution")
            fig = px.histogram(df, x="final_risk_score",
                               color="risk_level",
                               color_discrete_map={
                                   "HIGH": "red",
                                   "MEDIUM": "orange",
                                   "LOW": "green"
                               })
            st.plotly_chart(fig, use_container_width=True)

            # Anomalies by vendor
            st.subheader("Top Vendors by Risk Score")
            vendor_risk = df.groupby("vendor_id")["final_risk_score"].mean().reset_index()
            vendor_risk = vendor_risk.sort_values("final_risk_score", ascending=False).head(10)
            fig2 = px.bar(vendor_risk, x="vendor_id", y="final_risk_score")
            st.plotly_chart(fig2, use_container_width=True)

            # Full table
            st.subheader("All Records")
            st.dataframe(df, use_container_width=True)

        else:
            st.info("No records yet. Analyze some invoices first.")

    except Exception as e:
        st.error(f"API Error: {e}")

# ─── Payment Page 4: Payment History & Analytics ───
elif page == "Payment History & Analytics":
    st.header("Payment History & Analytics")

    try:
        stats = requests.get(f"{API_URL}/payment/stats").json()
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Payments", stats["total_records"])
        col2.metric("Total Anomalies", stats["total_anomalies"])
        col3.metric("Anomaly Rate", f"{stats['anomaly_percentage']}%")

        st.markdown("---")

        history = requests.get(f"{API_URL}/payment/history").json()

        if history:
            df = pd.DataFrame(history)

            st.subheader("Risk Score Distribution")
            fig = px.histogram(df, x="final_risk_score",
                               color="risk_level",
                               color_discrete_map={
                                   "HIGH": "red",
                                   "MEDIUM": "orange",
                                   "LOW": "green"
                               })
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Payment Method Distribution")
            method_counts = df["payment_method"].value_counts().reset_index()
            method_counts.columns = ["Payment Method", "Count"]
            fig2 = px.bar(method_counts, x="Payment Method", y="Count")
            st.plotly_chart(fig2, use_container_width=True)

            st.subheader("Top Vendors by Risk Score")
            vendor_risk = df.groupby("vendor_id")["final_risk_score"].mean().reset_index()
            vendor_risk = vendor_risk.sort_values("final_risk_score", ascending=False).head(10)
            fig3 = px.bar(vendor_risk, x="vendor_id", y="final_risk_score")
            st.plotly_chart(fig3, use_container_width=True)

            st.subheader("All Payment Records")
            st.dataframe(df, use_container_width=True)

        else:
            st.info("No payment records yet. Analyze some payments first.")

    except Exception as e:
        st.error(f"API Error: {e}")