import streamlit as st
import pandas as pd
import re

st.set_page_config(
    page_title="🚛 Mahindra Docket Audit Tool - CV",
    layout="centered"
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

# Normalize column names
normalized_columns = {col.strip().lower(): col for col in data.columns}


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

st.markdown("""
    <style>
    .table-wrapper { max-width: 700px; }
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
        border: 2px solid black;
    }
    .styled-table th, .styled-table td {
        border: 1px solid black;
        padding: 6px 12px;
    }
    .styled-table th {
        background-color: #004d40;
        color: white;
    }
    .styled-table td:first-child {
        background-color: #f7f7f7;
        font-weight: 600;
        text-align: left;
    }
    .styled-table td {
        white-space: nowrap;
        text-align: right;
    }
    </style>
""", unsafe_allow_html=True)

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

# --- Define Split ---
pricing_columns = []
for col in data.columns:
    if col in [variant_col, 'Model Name']:
        continue
    pricing_columns.append(col)
    if col.strip().lower() == 'on road price without smc road tax':
        break

cartel_lookup = [
    'm&m scheme with gst',
    'dealer offer ( without exchange case )',
    'dealer offer ( if exchange case )'
]

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
for lookup in cartel_lookup:
    actual_col = normalized_columns.get(lookup)
    val = row.get(actual_col) if actual_col else None
    val_display = val if pd.notnull(val) else "<i style='color:red;'>Invalid</i>"
    html_cartel += f"<tr><td>{actual_col if actual_col else lookup}</td><td>{val_display}</td></tr>"

html_cartel += "</table></div>"
st.markdown(html_cartel, unsafe_allow_html=True)
