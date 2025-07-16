import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- Cached Data Loading with Error Handling ---
@st.cache_data
def load_data():
    try:
        return pd.read_excel("PV Price List Master D. 08.07.2025.xlsx")
    except FileNotFoundError:
        st.error("Error: Pricing file not found. Please ensure 'PV Price List Master D. 08.07.2025.xlsx' exists in the app directory.")
        st.stop()

file_path = "PV Price List Master D. 08.07.2025.xlsx"
price_data = load_data()

# --- Main App (Original Visual Design) ---
st.set_page_config(
    page_title="Mahindra Pricing Viewer", 
    layout="centered",
    initial_sidebar_state="auto"
)

st.title("🚗 Mahindra Vehicle Pricing Viewer")

# --- Show Last Modified Timestamp ---
if os.path.exists(file_path):
    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%d-%b-%Y %I:%M %p")
    st.caption(f"📅 Data last updated on: {mod_time}")

# --- Original 3-Step Selection ---
model = st.selectbox("Select Model", sorted(price_data["Model"].unique()))

fuel_options = price_data[price_data["Model"] == model]["Fuel Type"].unique()
fuel_type = st.selectbox("Select Fuel Type", sorted(fuel_options))

filtered_variants = price_data[(price_data["Model"] == model) & (price_data["Fuel Type"] == fuel_type)]
variant_options = filtered_variants["Variant"].unique()
variant = st.selectbox("Select Variant", sorted(variant_options))

# --- Original Price Display ---
selected_row = price_data[(price_data["Model"] == model) &
                         (price_data["Fuel Type"] == fuel_type) &
                         (price_data["Variant"] == variant)]

if selected_row.empty:
    st.warning("No matching entry found for selected filters.")
else:
    st.markdown("---")
    st.subheader("📋 Vehicle Pricing Details")

    row = selected_row.iloc[0]

    def fmt(val, bold=False):
        formatted = f"₹{int(val):,}" if pd.notnull(val) else "<i style='color:gray;'>N/A</i>"
        return f"<b>{formatted}</b>" if bold else formatted

    # Shared pricing (single column)
    shared_fields = [
        ("Ex-Showroom Price", "Ex-Showroom Price"),
        ("TCS", "TCS 1%"),
        ("Comprehensive + ZeroDep. Insurance", "Insurance 1 Yr OD + 3 Yr TP + Zero Dep."),
        ("RSA (Road SideAssistance) For 1 Year", "RSA"),  # If column exists
        ("SMC Road - Tax (IfApplicable)", "SMC"),
        ("MAXI CARE", "Maxi Care"),
        ("Accessories", "Accessories Kit")
    ]

    # Registration-specific
    reg_fields = [
        ("RTO (W/O HYPO)", ("RTO (W/O HYPO) - Individual", "RTO (W/O HYPO) - Corporate")),
        ("RTO (With HYPO)", ("RTO (With HYPO) - Individual", "RTO (With HYPO) - Corporate")),
        ("On Road Price", ("On Road Price (With HYPO) - Individual", "On Road Price (With HYPO) - Corporate"))
    ]

    # --- HTML Table Styling ---
    html = """
    <style>
        .full-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 16px;
            margin-top: 16px;
        }
        .full-table th, .full-table td {
            border: 1px solid #666;
            padding: 8px 12px;
            text-align: center;
        }
        .full-table th {
            background-color: #f5f5f5;
            font-weight: bold;
        }
        .full-table td:first-child {
            text-align: left;
            font-weight: bold;
        }
    </style>

    <table class="full-table">
        <tr><th>Description</th><th>Amount</th></tr>
    """

    # Add shared pricing rows
    for label, key in shared_fields:
        value = fmt(row.get(key))
        html += f"<tr><td>{label}</td><td>{value}</td></tr>"

    html += "</table><br><br>"

    # --- Registration table (side-by-side) ---
    html += """
    <table class="full-table">
        <tr><th>Registration</th><th>Individual</th><th>Corporate</th></tr>
    """

    for label, (ind_key, corp_key) in reg_fields:
        is_on_road = "On Road" in label
        ind_val = fmt(row.get(ind_key), bold=is_on_road)
        corp_val = fmt(row.get(corp_key), bold=is_on_road)
        html += f"<tr><td>{label}</td><td>{ind_val}</td><td>{corp_val}</td></tr>"

    html += "</table>"

    st.markdown(html, unsafe_allow_html=True)
