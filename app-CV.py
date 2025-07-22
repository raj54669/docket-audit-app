import streamlit as st
import pandas as pd

# Page configuration
st.set_page_config(page_title="Mahindra Docket Audit Tool - CV")

# Title
st.title("🚛 Mahindra Commercial Vehicle Docket Audit")

# Load data from file inside the repo (no uploader)
file_path = "data/docket-cv.xlsx"  # <- Update if your file is in a different path
df = pd.read_excel(file_path)

# Vehicle variant selection
variant_column = "Select Vehicle Variant"
if variant_column not in df.columns:
    st.error(f"Column '{variant_column}' not found in Excel file.")
    st.stop()

variants = df[variant_column].dropna().unique()
selected_variant = st.selectbox("Select Vehicle Variant", sorted(variants))

# Filter selected row
selected_row = df[df[variant_column] == selected_variant]
if selected_row.empty:
    st.warning("No data found for the selected variant.")
    st.stop()

row = selected_row.iloc[0]  # Single matching row

# Pricing fields as per Excel header — DO NOT change field names
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

# Cartel Offer fields — restored
cartel_fields = [
    'M&M Scheme with GST',
    'Dealer Offer ( Without Exchange Case)',
    'Dealer Offer ( If Exchange Case)'
]

# VEHICLE PRICING SECTION
st.markdown("### 📄 Vehicle Pricing Details")
st.markdown("""
<table style="width:100%; border-collapse: collapse;">
    <thead>
        <tr style="background-color: #FF6600; color: white;">
            <th style="text-align: left; padding: 8px;">Description</th>
            <th style="text-align: left; padding: 8px;">Amount</th>
        </tr>
    </thead>
    <tbody>
""", unsafe_allow_html=True)

for field in pricing_fields:
    value = row.get(field)
    if pd.isnull(value) or value == "":
        value_display = "<i style='color: red;'>Missing</i>"
    else:
        value_display = f"₹{int(value):,}" if isinstance(value, (int, float)) else str(value)

    bg_color = "#E6F2FF" if pricing_fields.index(field) % 2 == 0 else "white"
    st.markdown(
        f"""
        <tr style="background-color: {bg_color};">
            <td style="padding: 8px;">{field}</td>
            <td style="padding: 8px;">{value_display}</td>
        </tr>
        """, unsafe_allow_html=True
    )

st.markdown("</tbody></table>", unsafe_allow_html=True)

# CARTEL OFFER SECTION
st.markdown("### 🎯 Cartel Offer")
st.markdown("""
<table style="width:100%; border-collapse: collapse;">
    <thead>
        <tr style="background-color: #8B0000; color: white;">
            <th style="text-align: left; padding: 8px;">Offer Type</th>
            <th style="text-align: left; padding: 8px;">Amount</th>
        </tr>
    </thead>
    <tbody>
""", unsafe_allow_html=True)

for field in cartel_fields:
    value = row.get(field)
    if pd.isnull(value) or value == "":
        value_display = "<i style='color: red;'>Missing</i>"
    else:
        value_display = f"₹{int(value):,}" if isinstance(value, (int, float)) else str(value)

    bg_color = "#FFF0F0" if cartel_fields.index(field) % 2 == 0 else "white"
    st.markdown(
        f"""
        <tr style="background-color: {bg_color};">
            <td style="padding: 8px;">{field}</td>
            <td style="padding: 8px;">{value_display}</td>
        </tr>
        """, unsafe_allow_html=True
    )

st.markdown("</tbody></table>", unsafe_allow_html=True)
