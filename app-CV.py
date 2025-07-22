import streamlit as st
import pandas as pd
import re

# --- Page Configuration ---
st.set_page_config(
    page_title="🚛 Mahindra Docket Audit Tool - CV",
    layout="centered",
    initial_sidebar_state="auto"
)

# --- Load Excel Data ---
@st.cache_data(show_spinner=False)
def load_data(file_path):
    try:
        return pd.read_excel(file_path, header=1)  # skip first row
    except Exception as e:
        st.error(f"❌ Failed to load Excel file: {e}")
        st.stop()

file_path = "Data/Discount_Cheker/CV Discount Check Master File 12.07.2025.xlsx"
data = load_data(file_path)

# --- Currency Formatter (Indian style) ---
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

# --- CSS Styling ---
st.markdown("""
    <style>
    .table-wrapper {
        max-width: 700px;
        margin-top: 1rem;
    }
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
        line-height: 1.2;
        border: 2px solid black;
    }
    .styled-table th, .styled-table td {
        border: 1px solid black;
        padding: 8px 12px;
    }
    .styled-table th {
        text-align: left;
    }
    .pricing-table td:first-child {
        background-color: #e3f2fd;
        font-weight: 600;
    }
    .pricing-table td:last-child {
        background-color: #bbdefb;
        text-align: right;
        white-space: nowrap;
    }
    .pricing-table th {
        background-color: #1976d2;
        color: white;
    }

    .offer-table td:first-child {
        background-color: #e8f5e9;
        font-weight: 600;
    }
    .offer-table td:last-child {
        background-color: #c8e6c9;
        text-align: right;
        white-space: nowrap;
    }
    .offer-table th {
        background-color: #388e3c;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- Title ---
st.title("🚛 Mahindra Docket Audit Tool - CV")

# --- Dropdown for Variant ---
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

# --- Vehicle Pricing Details Table ---
st.subheader("📋 Vehicle Pricing Details")

pricing_keys = [
    "Ex-Showroom Price",
    "TCS",
    "Comprehensive + ZeroDep. Insurance",
    "R.T.O. Charges WithHypo.",
    "RSA (Road SideAssistance) For 1Year",
    "SMC Road - Tax (IfApplicable)",
    "MAXI CARE",
    "Accessories",
    "ON ROAD PRICEWith SMC Road Tax",
    "ON ROAD PRICEWithout SMC RoadTax"
]

pricing_html = """
<div class="table-wrapper">
<table class="styled-table pricing-table">
    <tr><th>Description</th><th>Amount</th></tr>
"""

for key in pricing_keys:
    if key in row:
        val = format_indian_currency(row.get(key))
        pricing_html += f"<tr><td>{key}</td><td>{val}</td></tr>"

pricing_html += "</table></div>"
st.markdown(pricing_html, unsafe_allow_html=True)

# --- Cartel Offer Table ---
st.subheader("🎁 Cartel Offer")

cartel_keys = [
    "M&M Scheme with GST",
    "Dealer Offer ( Without Exchange Case)",
    "Dealer Offer ( If Exchange Case)"
]

cartel_html = """
<div class="table-wrapper">
<table class="styled-table offer-table">
    <tr><th>Description</th><th>Offer</th></tr>
"""

for key in cartel_keys:
    if key in row:
        val = row.get(key)
        if pd.isnull(val):
            val = "<i style='color:gray;'>N/A</i>"
        else:
            val = str(val)
        cartel_html += f"<tr><td>{key}</td><td>{val}</td></tr>"

cartel_html += "</table></div>"
st.markdown(cartel_html, unsafe_allow_html=True)
