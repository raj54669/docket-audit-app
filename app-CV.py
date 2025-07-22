import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="🚛 Mahindra Docket Audit Tool - CV", layout="centered")

# Load Excel
@st.cache_data(show_spinner=False)
def load_data(path):
    return pd.read_excel(path, header=1)

file_path = "Data/Discount_Cheker/CV Discount Check Master File 12.07.2025.xlsx"
data = load_data(file_path)

# Currency formatting
def format_indian_currency(value):
    try:
        if pd.isnull(value) or value == 0:
            return "₹0"
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
        return f"-{result}" if is_negative else result
    except:
        return "Invalid"

# Dropdown
st.title("🚛 Mahindra Docket Audit Tool - CV")

variant_col = "Variant"
if variant_col not in data.columns:
    st.error("❌ 'Variant' column not found.")
    st.stop()

variants = data[variant_col].dropna().drop_duplicates().tolist()


# 🔽 Custom styles for dropdown
st.markdown("""
<style>
/* Outer dropdown box */
div[data-baseweb="select"] {
    background-color: #fff8e1 !important;  /* light cream */
    border: 1px solid #e0c07f !important;
    border-radius: 6px !important;
    min-height: 38px !important;  /* compact height */
}

/* Selected text in dropdown */
div[data-baseweb="select"] div[role="combobox"] {
    font-weight: bold !important;
    color: black !important;
    min-height: 38px !important;  /* compact selected box */
    padding: 2px 8px !important;
}

/* Final touch: ensure selected text is always black in dark mode too */
div[data-baseweb="select"] div[role="combobox"] > div {
    color: black !important;
    font-weight: bold !important;
}

/* Dropdown list itself */
ul[role='listbox'] {
    padding: 0 !important;
}

/* Each dropdown option */
ul[role='listbox'] li {
    font-size: 14px !important;
    font-weight: bold !important;
    color: black !important;
    padding: 2px 8px !important;  /* compact spacing */
    margin: 0 !important;
}

/* Hover effect for options */
ul[role='listbox'] li:hover {
    background-color: #ffe0b2 !important;  /* soft cream hover */
    color: black !important;
}
</style>
""", unsafe_allow_html=True)

# 🔽 Your dropdown select box

selected_variant = st.selectbox(
    "🎯 Select Vehicle Variant",
    options=[{"label": v, "value": v} for v in variants],
    format_func=lambda x: x["label"],
    index=0,
    key="vehicle_variant"
)["value"]

filtered = data[data[variant_col] == selected_variant]

if filtered.empty:
    st.warning("⚠️ No data found for selected variant.")
    st.stop()

row = filtered.iloc[0]

# Columns to show
vehicle_columns = [
    'Ex-Showroom Price',
    'TCS',
    'Comprehensive + Zero\nDep. Insurance',
    'R.T.O. Charges With\nHypo.',
    'RSA (Road Side\nAssistance) For 1\nYear',
    'SMC Road - Tax (If\nApplicable)',
    'MAXI CARE',
    'Accessories',
    'ON ROAD PRICE\nWith SMC Road Tax',
    'ON ROAD PRICE\nWithout SMC Road\nTax',
]

cartel_columns = [
    'M&M\nScheme with\nGST',
    'Dealer Offer ( Without Exchange Case)',
    'Dealer Offer ( If Exchange Case)'
]

# --- VEHICLE PRICING TABLE ---
st.subheader("📝 Vehicle Pricing Details")
vehicle_html = """
<style>
.vtable {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 25px;
    font-weight: bold;
    font-size: 14px;
}
.vtable th {
    background-color: #01579b;
    color: white !important;
    padding: 4px 6px;
    text-align: right;
}
.vtable td {
    background-color: #e3f2fd;
    padding: 4px 6px;
    font-weight: bold;
    text-align: right;
    color: black !important;
}
.vtable td:first-child, .vtable th:first-child {
    text-align: left;
}
.vtable, .vtable th, .vtable td {
    border: 1px solid #000;
}
</style>
<table class='vtable'>
<tr><th>Description</th><th>Amount</th></tr>
"""

for col in vehicle_columns:
    if col in row:
        value = format_indian_currency(row[col])
        vehicle_html += f"<tr><td>{col}</td><td>{value}</td></tr>"

vehicle_html += "</table>"
st.markdown(vehicle_html, unsafe_allow_html=True)

# --- CARTEL OFFER TABLE ---
st.subheader("🎁 Cartel Offer")
cartel_html = """
<style>
.ctable {
    border-collapse: collapse;
    width: 100%;
    font-weight: bold;
    font-size: 14px;
}
.ctable th {
    background-color: #2e7d32;
    color: white !important;
    padding: 4px 6px;
    text-align: right;
}
.ctable td {
    background-color: #e8f5e9;
    padding: 4px 6px;
    font-weight: bold;
    text-align: right;
    color: black !important;
}
.ctable td:first-child, .ctable th:first-child {
    text-align: left;
}
.ctable, .ctable th, .ctable td {
    border: 1px solid #000;
}
</style>
<table class='ctable'>
<tr><th>Description</th><th>Offer</th></tr>
"""

for col in cartel_columns:
    if col in row:
        val = row[col]
        if col.strip() == "M&M\nScheme with\nGST":
            val = format_indian_currency(val)
        cartel_html += f"<tr><td>{col}</td><td>{val}</td></tr>"

cartel_html += "</table>"
st.markdown(cartel_html, unsafe_allow_html=True)
