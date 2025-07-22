import streamlit as st
import pandas as pd
from datetime import datetime
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
        return pd.read_excel(file_path, header=1)
    except Exception as e:
        st.error(f"❌ Failed to load Excel file: {e}")
        st.stop()

file_path = "Data/Discount_Cheker/CV Discount Check Master File 12.07.2025.xlsx"
data = load_data(file_path)

# --- Format Currency (Indian Style) ---
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
        result = f"₹{formatted}.00"
        return f"<b>{'-' if is_negative else ''}{result}</b>"
    except Exception:
        return "<i style='color:red;'>Invalid</i>"

# --- UI Title ---
st.title("🚛 Mahindra Docket Audit Tool - CV")

# --- Variant Dropdown ---
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

# --- Render Styled Output ---
html = f"""
<div style='max-width: 750px;'>

<h3 style='color: #E65100;'>📋 Vehicle Pricing Details</h3>
<table style='width: 100%; border-collapse: collapse; font-size: 14px;'>
    <tr style='background-color: #BBDEFB; font-weight: bold;'>
        <td style='border: 1px solid #000; padding: 8px;'>Ex-Showroom Price</td>
        <td style='border: 1px solid #000; padding: 8px;'>{format_indian_currency(row['Ex-Showroom Price'])}</td>
    </tr>
    <tr style='background-color: #E3F2FD;'>
        <td style='border: 1px solid #000; padding: 8px;'>TCS</td>
        <td style='border: 1px solid #000; padding: 8px;'>{format_indian_currency(row['TCS'])}</td>
    </tr>
    <tr style='background-color: #E3F2FD;'>
        <td style='border: 1px solid #000; padding: 8px;'>Comprehensive + ZeroDep. Insurance</td>
        <td style='border: 1px solid #000; padding: 8px;'>{format_indian_currency(row['Comprehensive + ZeroDep. Insurance'])}</td>
    </tr>
    <tr style='background-color: #E3F2FD;'>
        <td style='border: 1px solid #000; padding: 8px;'>R.T.O. Charges With Hypo.</td>
        <td style='border: 1px solid #000; padding: 8px;'>{format_indian_currency(row['R.T.O. Charges WithHypo.'])}</td>
    </tr>
    <tr style='background-color: #E3F2FD;'>
        <td style='border: 1px solid #000; padding: 8px;'>RSA (Road Side Assistance) For 1 Year</td>
        <td style='border: 1px solid #000; padding: 8px;'>{format_indian_currency(row['RSA (Road SideAssistance) For 1Year'])}</td>
    </tr>
    <tr style='background-color: #E3F2FD;'>
        <td style='border: 1px solid #000; padding: 8px;'>SMC Road - Tax (If Applicable)</td>
        <td style='border: 1px solid #000; padding: 8px;'>{format_indian_currency(row['SMC Road - Tax (IfApplicable)'])}</td>
    </tr>
    <tr style='background-color: #E3F2FD;'>
        <td style='border: 1px solid #000; padding: 8px;'>MAXI CARE</td>
        <td style='border: 1px solid #000; padding: 8px;'>{format_indian_currency(row['MAXI CARE'])}</td>
    </tr>
    <tr style='background-color: #E3F2FD;'>
        <td style='border: 1px solid #000; padding: 8px;'>Accessories</td>
        <td style='border: 1px solid #000; padding: 8px;'>{format_indian_currency(row['Accessories'])}</td>
    </tr>
    <tr style='background-color: #90CAF9; font-weight: bold;'>
        <td style='border: 1px solid #000; padding: 8px;'>ON ROAD PRICE With SMC Road Tax</td>
        <td style='border: 1px solid #000; padding: 8px;'>{format_indian_currency(row['ON ROAD PRICEWith SMC Road Tax'])}</td>
    </tr>
    <tr style='background-color: #90CAF9; font-weight: bold;'>
        <td style='border: 1px solid #000; padding: 8px;'>ON ROAD PRICE Without SMC Road Tax</td>
        <td style='border: 1px solid #000; padding: 8px;'>{format_indian_currency(row['ON ROAD PRICEWithout SMC RoadTax'])}</td>
    </tr>
</table>

<h3 style='margin-top: 40px; color: #2E7D32;'>📦 Cartel Offer</h3>
<table style='width: 100%; border-collapse: collapse; font-size: 14px;'>
    <tr style='background-color: #C8E6C9; font-weight: bold;'>
        <td style='border: 1px solid #000; padding: 8px;'>M&M Scheme with GST</td>
        <td style='border: 1px solid #000; padding: 8px;'>₹25,000.00</td>
    </tr>
    <tr style='background-color: #E8F5E9;'>
        <td style='border: 1px solid #000; padding: 8px;'>Dealer Offer (Without Exchange Case)</td>
        <td style='border: 1px solid #000; padding: 8px;'>50% INSURANCE FREE + 12K ACCESSORIES PACK FREE</td>
    </tr>
    <tr style='background-color: #E8F5E9;'>
        <td style='border: 1px solid #000; padding: 8px;'>Dealer Offer (If Exchange Case)</td>
        <td style='border: 1px solid #000; padding: 8px;'>50% INSURANCE FREE</td>
    </tr>
</table>

</div>
"""

st.markdown(html, unsafe_allow_html=True)
