import streamlit as st
import pandas as pd

# --- Styling ---
st.set_page_config(page_title="Mahindra Docket Audit Tool - CV", layout="wide")

st.markdown("""
    <style>
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 16px;
    }
    .styled-table th, .styled-table td {
        border: 1px solid #000;
        padding: 8px;
        text-align: left;
    }
    .styled-table th {
        background-color: #FF6F00;
        color: white;
    }
    .styled-table tr:nth-child(even) {
        background-color: #f2f2f2;
    }
    .styled-table tr:hover {
        background-color: #e6f7ff;
    }
    </style>
""", unsafe_allow_html=True)


# --- Helper ---
def format_indian_currency(amount):
    try:
        if pd.isnull(amount):
            return "<i style='color:red;'>Missing</i>"
        amount = float(str(amount).replace(',', ''))
        s = f"{amount:,.2f}"
        return f"₹{s}"
    except:
        return "<i style='color:red;'>Invalid</i>"


# --- File Load ---
file_path = "your_file.xlsx"  # Replace with your actual Excel file path
df = pd.read_excel(file_path)

# --- Variant Selector ---
variant_column = "Select Vehicle Variant"
variant_options = df[variant_column].dropna().unique()
selected_variant = st.selectbox("🔷 Select Vehicle Variant", sorted(variant_options))

filtered_row = df[df[variant_column] == selected_variant]

if not filtered_row.empty:
    row = filtered_row.iloc[0]

    # --- Define Fields (must match Excel headers exactly) ---
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

    cartel_fields = [
        'M&M Scheme with GST',
        'Dealer Offer ( Without Exchange Case)',
        'Dealer Offer ( If Exchange Case)'
    ]

    # --- Vehicle Pricing Section ---
    st.markdown("### 🧾 <span style='color:#E65100;'>Vehicle Pricing Details</span>", unsafe_allow_html=True)

    html = "<table class='styled-table'><tr><th>Description</th><th>Amount</th></tr>"
    for field in pricing_fields:
        val = row.get(field, None)
        formatted = format_indian_currency(val) if pd.notnull(val) else "<i style='color:red;'>Missing</i>"
        html += f"<tr><td>{field}</td><td>{formatted}</td></tr>"
    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)

    # --- Cartel Offer Section ---
    st.markdown("### 📦 <span style='color:green;'>Cartel Offer</span>", unsafe_allow_html=True)

    html2 = "<table class='styled-table'><tr><th>Description</th><th>Offer</th></tr>"
    for field in cartel_fields:
        val = row.get(field, None)
        formatted = str(val) if pd.notnull(val) else "<i style='color:red;'>Missing</i>"
        html2 += f"<tr><td>{field}</td><td>{formatted}</td></tr>"
    html2 += "</table>"
    st.markdown(html2, unsafe_allow_html=True)

else:
    st.warning("No data found for the selected variant.")
