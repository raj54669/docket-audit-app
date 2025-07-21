# file: app.py

import streamlit as st
import pandas as pd
import re

st.set_page_config(
    page_title="🚛 Mahindra Docket Audit Tool - CV",
    layout="centered",
    initial_sidebar_state="auto"
)

@st.cache_data(show_spinner=False)
def load_data(file_path):
    try:
        return pd.read_excel(file_path, header=1)
    except Exception as e:
        st.error(f"❌ Failed to load Excel file: {e}")
        st.stop()

file_path = "Data/Discount_Cheker/CV Discount Check Master File 12.07.2025.xlsx"
data = load_data(file_path)

def format_indian_currency(value):
    try:
        if pd.isnull(value):
            return "<i style='color:gray;'>N/A</i>"
        value = float(value)
        is_negative = value < 0
        value = abs(value)
        s = f"{int(value)}"
        last_three = s[-3:]
        other = s[:-3]
        if other:
            other = re.sub(r'(\d)(?=(\d{2})+$)', r'\1,', other)
            formatted = f"{other},{last_three}"
        else:
            formatted = last_three
        result = f"₹{formatted}"
        return f"<b>{'-' if is_negative else ''}{result}</b>"
    except Exception:
        return "<i style='color:red;'>Invalid</i>"

st.title("🚛 Mahindra Docket Audit Tool - CV")

variant_col = 'Variant'
if variant_col not in data.columns:
    st.error("❌ 'Variant' column not found in the Excel file.")
    st.stop()

variants = data[variant_col].dropna().drop_duplicates().tolist()
selected_variant = st.selectbox("📘 Select Vehicle Variant", variants)

filtered_row = data[data[variant_col] == selected_variant]
if filtered_row.empty:
    st.warning("⚠️ No data found for selected variant.")
    st.stop()

row = filtered_row.iloc[0]

# --- Split Tables ---
pricing_columns = []
cartel_columns = []

found_gst = False
for col in data.columns:
    if col in [variant_col, 'Model Name']:
        continue
    if not found_gst:
        pricing_columns.append(col)
        if col == "M&M Scheme with GST":
            found_gst = True
    else:
        cartel_columns.append(col)

# --- Pricing Table ---
st.subheader("📋 Vehicle Pricing Details")
html_pricing = """
<div class="table-wrapper">
<table class="styled-table">
    <tr><th>Description</th><th>Amount</th></tr>
"""
for col in pricing_columns:
    val = format_indian_currency(row.get(col))
    html_pricing += f"<tr><td>{col}</td><td>{val}</td></tr>"
html_pricing += "</table></div>"
st.markdown(html_pricing, unsafe_allow_html=True)

# --- Cartel Offer Table ---
st.subheader("🛒 Cartel Offer")
html_cartel = """
<div class="table-wrapper">
<table class="styled-table">
    <tr><th>Description</th><th>Offer</th></tr>
"""
for col in cartel_columns:
    val = row.get(col)
    val_display = val if pd.notnull(val) else "<i style='color:red;'>Invalid</i>"
    html_cartel += f"<tr><td>{col}</td><td>{val_display}</td></tr>"
html_cartel += "</table></div>"
st.markdown(html_cartel, unsafe_allow_html=True)
