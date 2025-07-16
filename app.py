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

    # --- Fields (same as Excel) ---
    shared_fields = [
        "Ex-Showroom Price",
        "TCS 1%",
        "Insurance 1 Yr OD + 3 Yr TP + Zero Dep.",
        "Accessories Kit",
        "SMC",
        "Extended Warranty",
        "Maxi Care",
        "RSA (1 Year)",
        "Fastag"
    ]

    grouped_fields = [
        "RTO (W/O HYPO)",
        "RTO (With HYPO)",
        "On Road Price (W/O HYPO)",
        "On Road Price (With HYPO)"
    ]

    # --- Column keys for grouped fields ---
    group_keys = {
        "RTO (W/O HYPO)": (
            "RTO (W/O HYPO) - Individual", 
            "RTO (W/O HYPO) - Corporate"
        ),
        "RTO (With HYPO)": (
            "RTO (With HYPO) - Individual", 
            "RTO (With HYPO) - Corporate"
        ),
        "On Road Price (W/O HYPO)": (
            "On Road Price (W/O HYPO) - Individual", 
            "On Road Price (W/O HYPO) - Corporate"
        ),
        "On Road Price (With HYPO)": (
            "On Road Price (With HYPO) - Individual", 
            "On Road Price (With HYPO) - Corporate"
        )
    }

    # --- Styling ---
    html = """
    <style>
        .full-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 16px;
            margin: 0;
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
        .gapless-section {
            margin-bottom: 0;
        }
    </style>

    <table class="full-table gapless-section">
        <tr><th>Description</th><th>Amount</th></tr>
    """

    for field in shared_fields:
        val = row.get(field)
        html += f"<tr><td>{field}</td><td>{fmt(val)}</td></tr>"

    html += """
    </table>
    <table class="full-table">
        <tr><th>Registration</th><th>Individual</th><th>Corporate</th></tr>
    """

    for label in grouped_fields:
        ind_key, corp_key = group_keys[label]
        is_onroad = "On Road" in label
        ind_val = fmt(row.get(ind_key), bold=is_onroad)
        corp_val = fmt(row.get(corp_key), bold=is_onroad)
        html += f"<tr><td>{label}</td><td>{ind_val}</td><td>{corp_val}</td></tr>"

    html += "</table>"

    st.markdown(html, unsafe_allow_html=True)
