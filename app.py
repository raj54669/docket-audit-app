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

    display_fields = [
        "Ex-Showroom Price",
        "TCS 1%",
        "Insurance 1 Yr OD + 3 Yr TP + Zero Dep.",
        "Accessories Kit",
        "SMC",
        "Extended Warranty",
        "Maxi Care"
    ]

    pricing_html = "<ul>"
    for field in display_fields:
        value = selected_row.iloc[0].get(field, None)
        if pd.notnull(value):
            amount = f"₹{int(value):,}"
        else:
            amount = "<i style='color:gray;'>Not Available</i>"
        pricing_html += f"<li><strong>{field}</strong>: {amount}</li>"
    pricing_html += "</ul>"
    st.markdown(pricing_html, unsafe_allow_html=True)

if selected_row.empty:
    st.warning("No matching entry found for selected filters.")
else:
    st.markdown("---")
    st.subheader("📋 Side-by-Side Pricing Comparison")

    row = selected_row.iloc[0]

    # --- Format currency ---
    def fmt(val):
        return f"₹{int(val):,}" if pd.notnull(val) else "<i style='color:gray;'>N/A</i>"

    # --- Define fields and keys ---
    pricing_fields = [
        ("Ex-Showroom Price", "Ex-Showroom Price"),
        ("TCS 1%", "TCS 1%"),
        ("Insurance", "Insurance 1 Yr OD + 3 Yr TP + Zero Dep."),
        ("Accessories", "Accessories Kit"),
        ("SMC", "SMC"),
        ("Extended Warranty", "Extended Warranty"),
        ("Maxi Care", "Maxi Care"),
        ("RTO (W/O HYPO)", ("RTO (W/O HYPO) - Individual", "RTO (W/O HYPO) - Corporate")),
        ("RTO (With HYPO)", ("RTO (With HYPO) - Individual", "RTO (With HYPO) - Corporate")),
        ("On Road Price", ("On Road Price - Individual", "On Road Price - Corporate"))
    ]

    # --- HTML table styling with dark mode support ---
    comparison_html = """
    <style>
        .side-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            font-size: 16px;
        }
        .side-table th, .side-table td {
            border: 1px solid rgba(120, 120, 120, 0.5);
            padding: 10px;
            text-align: center;
        }
        .side-table th {
            background-color: rgba(0, 77, 64, 0.85);
            color: #ffffff;
        }
        .side-table td:first-child {
            text-align: left;
            font-weight: bold;
            background-color: rgba(224, 242, 241, 0.08);
            color: inherit;
        }
        .side-table td {
            background-color: rgba(255, 255, 255, 0.02);
            color: inherit;
        }
    </style>

    <table class="side-table">
        <tr>
            <th>Component</th>
            <th>Individual</th>
            <th>Corporate</th>
        </tr>
    """

    # --- Build table rows ---
    for label, key in pricing_fields:
        if isinstance(key, tuple):
            ind_val = fmt(row.get(key[0]))
            corp_val = fmt(row.get(key[1]))
        else:
            value = fmt(row.get(key))
            ind_val = corp_val = value
        comparison_html += f"<tr><td>{label}</td><td>{ind_val}</td><td>{corp_val}</td></tr>"

    comparison_html += "</table>"

    # --- Show table ---
    st.markdown(comparison_html, unsafe_allow_html=True)
