import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

@st.cache_data
def load_data():
    try:
        return pd.read_excel("PV Price List Master D. 08.07.2025.xlsx")
    except FileNotFoundError:
        st.error("❌ Pricing file not found.")
        st.stop()

file_path = "PV Price List Master D. 08.07.2025.xlsx"
price_data = load_data()

st.set_page_config(
    page_title="Mahindra Pricing Viewer",
    layout="centered",
    initial_sidebar_state="auto"
)

st.title("🚗 Mahindra Vehicle Pricing Viewer")

# --- Timestamp in IST ---
if os.path.exists(file_path):
    ist_time = datetime.fromtimestamp(os.path.getmtime(file_path)) + timedelta(hours=5, minutes=30)
    st.caption(f"📅 Data last updated on: {ist_time.strftime('%d-%b-%Y %I:%M %p')} (IST)")

# --- Dropdowns ---
model = st.selectbox("Select Model", sorted(price_data["Model"].unique()))
fuel_type = st.selectbox("Select Fuel Type", sorted(price_data[price_data["Model"] == model]["Fuel Type"].unique()))
variant = st.selectbox("Select Variant", sorted(price_data[(price_data["Model"] == model) & (price_data["Fuel Type"] == fuel_type)]["Variant"].unique()))
selected_row = price_data[(price_data["Model"] == model) & (price_data["Fuel Type"] == fuel_type) & (price_data["Variant"] == variant)]

# --- Formatting Helper ---
def fmt(val, bold=False):
    formatted = f"₹{int(val):,}" if pd.notnull(val) else "<i style='color:gray;'>N/A</i>"
    return f"<b>{formatted}</b>" if bold else formatted

if selected_row.empty:
    st.warning("No data found for selected filters.")
else:
    st.subheader("📋 Vehicle Pricing Details")
    row = selected_row.iloc[0]

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
        "On Road Price (W/O HYPO)": ("On Road Price (W/O HYPO) - Individual", "On Road Price (W/O HYPO) - Corporate"),
        "On Road Price (With HYPO)": ("On Road Price (With HYPO) - Individual", "On Road Price (With HYPO) - Corporate"),
    }

    # --- Updated CSS with tighter table layout ---
    html = """
    <style>
        .table-wrapper {
            border: 2px solid black;
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 0px;
            display: inline-block;
        }

        .styled-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 16px;
        }

        .styled-table th, .styled-table td {
            border: 1px solid black;
            padding: 10px 12px;
            text-align: center;
        }

        .styled-table th {
            background-color: #004d40;
            color: white;
            font-weight: bold;
        }

        .styled-table td:first-child {
            text-align: left;
            font-weight: 600;
            background-color: #f7f7f7;
        }

        .styled-table td {
            background-color: white;
        }

        /* Dark Mode */
        @media (prefers-color-scheme: dark) {
            .table-wrapper {
                border: 2px solid white;
            }

            .styled-table td {
                background-color: #111;
                color: #eee;
            }

            .styled-table td:first-child {
                background-color: #1e1e1e;
                color: white;
            }

            .styled-table th, .styled-table td {
                border: 1px solid white;
            }
        }
    </style>
    """

    # --- First Table ---
    html += """
    <div class="table-wrapper">
    <table class="styled-table">
        <tr><th>Description</th><th>Amount</th></tr>
    """
    for field in shared_fields:
        html += f"<tr><td>{field}</td><td>{fmt(row.get(field))}</td></tr>"
    html += "</table></div>"

    # --- Second Table ---
    html += """
    <div class="table-wrapper">
    <table class="styled-table">
        <tr><th>Registration</th><th>Individual</th><th>Corporate</th></tr>
    """
    for field in grouped_fields:
        ind_key, corp_key = group_keys[field]
        is_onroad = "On Road" in field
        html += f"<tr><td>{field}</td><td>{fmt(row.get(ind_key), is_onroad)}</td><td>{fmt(row.get(corp_key), is_onroad)}</td></tr>"
    html += "</table></div>"

    st.markdown(html, unsafe_allow_html=True)
