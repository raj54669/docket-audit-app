import streamlit as st
import pandas as pd
import os
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
        df = pd.read_excel(file_path, header=1)
        df.columns = df.columns.str.strip()  # ensure no accidental spaces
        return df
    except Exception as e:
        st.error(f"❌ Failed to load Excel file: {e}")
        st.stop()

file_path = "Data/Discount_Cheker/CV Discount Check Master File 12.07.2025.xlsx"
data = load_data(file_path)

# --- Currency Formatter (Indian style) ---
def format_indian_currency(value):
    try:
        if pd.isnull(value):
            return "<i style='color:red;'>Missing</i>"
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

# --- Safe getter for missing keys ---
def get_value_safe(row, col):
    try:
        return format_indian_currency(row[col])
    except KeyError:
        return "<i style='color:red;'>Missing</i>"

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

# --- Fields to Display (use exact headers from Excel) ---
fields_to_display = [
    'Ex-Showroom Price',
    'TCS',
    'Comprehensive + ZeroDep. Insurance',
    'R.T.O. Charges With Hypo.',
    'RSA (Road Side Assistance) For 1 Year',
    'SMC Road - Tax (If Applicable)',
    'MAXI CARE',
    'Accessories',
    'ON ROAD PRICE With SMC Road Tax',
    'ON ROAD PRICE Without SMC Road Tax',
]

# --- Styling ---
st.markdown("""
    <style>
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
    }
    .styled-table th, .styled-table td {
        border: 1px solid #000;
        padding: 8px 12px;
    }
    .styled-table th {
        background-color: #FF6F00;
        color: white;
        text-align: left;
    }
    .styled-table tr:nth-child(even) td {
        background-color: #E3F2FD;
    }
    .styled-table tr:last-child td {
        background-color: #90CAF9;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- Vehicle Pricing Table ---
st.markdown("### 🧾 <span style='color:#E65100;'>Vehicle Pricing Details</span>", unsafe_allow_html=True)

html = "<table class='styled-table'><tr><th>Description</th><th>Amount</th></tr>"

for field in fields_to_display:
    val = get_value_safe(row, field)
    html += f"<tr><td>{field}</td><td>{val}</td></tr>"

html += "</table>"
st.markdown(html, unsafe_allow_html=True)
