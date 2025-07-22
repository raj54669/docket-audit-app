import streamlit as st
import pandas as pd
import re

# --- Page Configuration ---
st.set_page_config(
    page_title="🚛 Mahindra Docket Audit Tool - CV",
    layout="centered"
)

# --- Load Excel Data ---
@st.cache_data(show_spinner=False)
def load_data(path):
    return pd.read_excel(path, header=1)

file_path = "Data/Discount_Cheker/CV Discount Check Master File 12.07.2025.xlsx"
data = load_data(file_path)

# --- Currency Formatter ---
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

# --- Title ---
st.title("🚛 Mahindra Docket Audit Tool - CV")

# --- Select Variant ---
variant_col = "Variant"
if variant_col not in data.columns:
    st.error("❌ 'Variant' column not found.")
    st.stop()

variants = data[variant_col].dropna().drop_duplicates().tolist()
selected_variant = st.selectbox("🔷 Select Vehicle Variant", variants)

filtered = data[data[variant_col] == selected_variant]
if filtered.empty:
    st.warning("⚠️ No data found for selected variant.")
    st.stop()

row = filtered.iloc[0]

# --- Column Grouping ---
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

# --- Section: Vehicle Pricing Details ---
st.subheader("📝 Vehicle Pricing Details")
vehicle_html = """
<style>
.vtable th {
    background-color: #01579b;
    color: white;
    padding: 8px;
}
.vtable td {
    background-color: #e3f2fd;
    padding: 8px;
}
.vtable {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 30px;
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

# --- Section: Cartel Offer ---
st.subheader("🎁 Cartel Offer")
cartel_html = """
<style>
.ctable th {
    background-color: #2e7d32;
    color: white;
    padding: 8px;
}
.ctable td {
    background-color: #e8f5e9;
    padding: 8px;
}
.ctable {
    border-collapse: collapse;
    width: 100%;
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
        value = row[col] if pd.notnull(row[col]) else "—"
        cartel_html += f"<tr><td>{col}</td><td>{value}</td></tr>"

cartel_html += "</table>"
st.markdown(cartel_html, unsafe_allow_html=True)
