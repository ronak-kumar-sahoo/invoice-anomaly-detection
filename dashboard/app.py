import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import json

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Invoice Anomaly Detection",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Invoice & Payment Anomaly Detection System")
st.markdown("---")

# Sidebar
page = st.sidebar.selectbox("Go to", [
    "Single Invoice Check",
    "Document Upload (PDF/Image)",
    "Bulk CSV Upload",
    "History & Analytics"
])

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