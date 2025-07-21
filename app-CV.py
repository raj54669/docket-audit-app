import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="CV Discount Viewer",
    layout="centered",
    initial_sidebar_state="auto"
)

# --- Load Excel Data ---
@st.cache_data(show_spinner=False)
def load_data(file_path):
    try:
        return pd.read_excel(file_path)
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

# --- Styling ---
st.markdown("""
    <style>
    .styled-table {
        width: 100%; border-collapse: collapse; table-layout: fixed;
        font-size: 14px; line-height: 1; border: 2px solid black;
    }
    .styled-table th, .styled-table td {
        border: 1px solid black; padding: 6px 10px; text-align: left;
    }
    .styled-table th {
        background-color: #004d40; color: white;
    }
    .styled-table td:first-child {
        font-weight: 600; background-color: #f7f7f7;
    }
    </style>
""", unsafe_allow_html=True)

# --- Title ---
st.title("🚛 CV Discount Pricing Viewer")

# --- Dropdown for Variant ---
variants = sorted(data['Variant'].dropna().unique())
selected_variant = st.selectbox("🔽 Select Vehicle Variant", variants)

filtered_row = data[data['Variant'] == selected_variant]
if filtered_row.empty:
    st.warning("⚠️ No data found for selected variant.")
    st.stop()

row = filtered_row.iloc[0]

# --- Render Table ---
st.subheader("📋 Vehicle Pricing Details")

html = """
<div class="table-wrapper">
<table class="styled-table">
    <tr><th>Description</th><th>Amount</th></tr>
"""

for col in data.columns:
    if col != 'Variant':
        val = format_indian_currency(row.get(col))
        html += f"<tr><td>{col}</td><td>{val}</td></tr>"

html += "</table></div>"
st.markdown(html, unsafe_allow_html=True)
