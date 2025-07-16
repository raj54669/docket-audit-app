import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# --- Cached Data Loading with Error Handling ---
@st.cache_data
def load_data():
    try:
        return pd.read_excel("PV Price List Master D. 08.07.2025.xlsx")
    except FileNotFoundError:
        st.error("❌ Pricing file not found.")
        st.stop()

file_path = "PV Price List Master D. 08.07.2025.xlsx"
price_data = load_data()

# --- Streamlit Page Setup ---
st.set_page_config(
    page_title="Mahindra Pricing Viewer",
    layout="centered",
    initial_sidebar_state="auto"
)

st.title("🚗 Mahindra Vehicle Pricing Viewer")

# --- Last Modified Timestamp in IST ---
if os.path.exists(file_path):
    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path)) + timedelta(hours=5, minutes=30)
    st.caption(f"📅 Data last updated on: {mod_time.strftime('%d-%b-%Y %I:%M %p')} (IST)")

# --- Model Selection ---
model = st.selectbox("Select Model", sorted(price_data["Model"].unique()))
fuel_options = price_data[price_data["Model"] == model]["Fuel Type"].unique()
fuel_type = st.selectbox("Select Fuel Type", sorted(fuel_options))
variant_options = price_data[(price_data["Model"] == model) & 
                             (price_data["Fuel Type"] == fuel_type)]["Variant"].unique()
variant = st.selectbox("Select Variant", sorted(variant_options))

# --- Retrieve Selected Row ---
selected_row = price_data[
    (price_data["Model"] == model) &
    (price_data["Fuel Type"] == fuel_type) &
    (price_data["Variant"] == variant)
]

if selected_row.empty:
    st.warning("No matching data found.")
else:
    st.subheader("📋 Vehicle Pricing Details")
    row = selected_row.iloc[0]

    def fmt(val, bold=False):
        formatted = f"₹{int(val):,}" if pd.notnull(val) else "<i style='color:gray;'>N/A</i>"
        return f"<b>{formatted}</b>" if bold else formatted

    # --- Columns as per Excel ---
    shared_fields = [
        "Ex-Showroom Price", "TCS 1%", "Insurance 1 Yr OD + 3 Yr TP + Zero Dep.",
        "Accessories Kit", "SMC", "Extended Warranty", "Maxi Care", "RSA (1 Year)", "Fastag"
    ]

    grouped_fields = [
        "RTO (W/O HYPO)", "RTO (With HYPO)",
        "On Road Price (W/O HYPO)", "On Road Price (With HYPO)"
    ]

    group_keys = {
        "RTO (W/O HYPO)": ("RTO (W/O HYPO) - Individual", "RTO (W/O HYPO) - Corporate"),
        "RTO (With HYPO)": ("RTO (With HYPO) - Individual", "RTO (With HYPO) - Corporate"),
        "On Road Price (W/O HYPO)": (
            "On Road Price (W/O HYPO) - Individual", "On Road Price (W/O HYPO) - Corporate"),
        "On Road Price (With HYPO)": (
            "On Road Price (With HYPO) - Individual", "On Road Price (With HYPO) - Corporate"),
    }

    # --- HTML Table Styling ---
    html = """
    <style>
        .styled-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 16px;
            margin-bottom: 16px;
            border: 2px solid #004d40;
            border-radius: 12px;
            overflow: hidden;
        }
        .styled-table th, .styled-table td {
            padding: 10px 12px;
            border: 1px solid #999;
            text-align: center;
        }
        .styled-table th {
            background-color: #004d40;
            color: white;
        }
        .styled-table td:first-child {
            text-align: left;
            font-weight: 600;
            background-color: #f2f2f2;
        }
        .styled-table td {
            background-color: white;
        }

        /* Rounded corners */
        .styled-table tr:first-child th:first-child {
            border-top-left-radius: 12px;
        }
        .styled-table tr:first-child th:last-child {
            border-top-right-radius: 12px;
        }
        .styled-table tr:last-child td:first-child {
            border-bottom-left-radius: 12px;
        }
        .styled-table tr:last-child td:last-child {
            border-bottom-right-radius: 12px;
        }

        /* Dark Mode */
        @media (prefers-color-scheme: dark) {
            .styled-table td {
                background-color: #111;
                color: #eee;
            }
            .styled-table td:first-child {
                background-color: #1a1a1a;
            }
        }
    </style>
    """

    # --- First Table: Description + Amount ---
    html += """
    <table class="styled-table">
        <tr><th>Description</th><th>Amount</th></tr>
    """
    for field in shared_fields:
        val = row.get(field)
        html += f"<tr><td>{field}</td><td>{fmt(val)}</td></tr>"
    html += "</table>"

    # --- Second Table: RTO / On-Road Price ---
    html += """
    <table class="styled-table">
        <tr><th>Registration</th><th>Individual</th><th>Corporate</th></tr>
    """
    for label in grouped_fields:
        ind_key, corp_key = group_keys[label]
        is_onroad = "On Road" in label
        ind_val = fmt(row.get(ind_key), bold=is_onroad)
        corp_val = fmt(row.get(corp_key), bold=is_onroad)
        html += f"<tr><td>{label}</td><td>{ind_val}</td><td>{corp_val}</td></tr>"
    html += "</table>"

    # --- Display Tables ---
    st.markdown(html, unsafe_allow_html=True)
