import streamlit as st
import pandas as pd

st.set_page_config(page_title="Mahindra Docket Audit Tool - CV")  # Default layout only

# --- File Upload ---
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # --- Dropdown for variant ---
    variant_column = "Select Vehicle Variant"
    if variant_column not in df.columns:
        st.error(f"Missing required column: {variant_column}")
    else:
        variants = df[variant_column].dropna().unique()
        selected_variant = st.selectbox("Select Vehicle Variant", sorted(variants))

        row = df[df[variant_column] == selected_variant].iloc[0]

        # --- Pricing Fields (exact Excel headers) ---
        pricing_fields = [
            'Ex-Showroom Price',
            'TCS',
            'Comprehensive + ZeroDep. Insurance',
            'R.T.O. Charges With Hypo.',
            'RSA (Road Side Assistance) For 1 Year',
            'SMC Road - Tax (If Applicable)',
            'MAXI CARE',
            'Accessories',
            'ON ROAD PRICE With SMC Road Tax',
            'ON ROAD PRICE Without SMC Road Tax'
        ]

        # --- Cartel Offer Fields (exact Excel headers) ---
        cartel_fields = [
            'M&M Scheme with GST',
            'Dealer Offer ( Without Exchange Case)',
            'Dealer Offer ( If Exchange Case)'
        ]

        # --- Pricing Section ---
        st.markdown("### 🧾 Vehicle Pricing Details")
        for field in pricing_fields:
            value = row.get(field)
            display = f"₹{value:,.2f}" if pd.notnull(value) else "*Missing*"
            st.write(f"**{field}**: {display}")

        # --- Cartel Offer Section ---
        st.markdown("### 📦 Cartel Offer")
        for field in cartel_fields:
            value = row.get(field)
            display = str(value) if pd.notnull(value) else "*Missing*"
            st.write(f"**{field}**: {display}")
