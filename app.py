import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- Load Excel File ---
@st.cache_data
def load_data():
    try:
        return pd.read_excel("PV Price List Master D. 08.07.2025.xlsx")
    except FileNotFoundError:
        st.error("Error: Pricing file not found.")
        st.stop()

file_path = "PV Price List Master D. 08.07.2025.xlsx"
price_data = load_data()

# --- Streamlit Setup ---
st.set_page_config(
    page_title="Mahindra Pricing Viewer",
    layout="centered",
    initial_sidebar_state="auto"
)

st.title("🚗 Mahindra Vehicle Pricing Viewer")

# --- File Timestamp ---
if os.path.exists(file_path):
    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%d-%b-%Y %I:%M %p")
    st.caption(f"📅 Data last updated on: {mod_time}")

# --- 3-Step Filter ---
model = st.selectbox("Select Model", sorted(price_data["Model"].unique()))
fuel_options = price_data[price_data["Model"] == model]["Fuel Type"].unique()
fuel_type = st.selectbox("Select Fuel Type", sorted(fuel_options))
variant_options = price_data[(price_data["Model"] == model) & 
                             (price_data["Fuel Type"] == fuel_type)]["Variant"].unique()
variant = st.selectbox("Select Variant", sorted(variant_options))

# --- Extract Selection ---
selected_row = price_data[
    (price_data["Model"] == model) &
    (price_data["Fuel Type"] == fuel_type) &
    (price_data["Variant"] == variant)
]

# --- Display Table ---
if selected_row.empty:
    st.warning("No matching entry found for selected filters.")
else:
    st.subheader("📋 Vehicle Pricing Details")
    row = selected_row.iloc[0]

    def fmt(val, bold=False):
        formatted = f"₹{int(val):,}" if pd.notnull(val) else "<i style='color:gray;'>N/A</i>"
        return f"<b>{formatted}</b>" if bold else formatted

    # --- Fields ---
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

    group_keys = {
        "RTO (W/O HYPO)": (
            "RTO (W/O HYPO) - Individual", "RTO (W/O HYPO) - Corporate"
        ),
        "RTO (With HYPO)": (
            "RTO (With HYPO) - Individual", "RTO (With HYPO) - Corporate"
        ),
        "On Road Price (W/O HYPO)": (
            "On Road Price (W/O HYPO) - Individual", "On Road Price (W/O HYPO) - Corporate"
        ),
        "On Road Price (With HYPO)": (
            "On Road Price (With HYPO) - Individual", "On Road Price (With HYPO) - Corporate"
        )
    }

    # --- Table HTML Styling ---
    html = """
    <style>
        .full-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 16px;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }
        .full-table th, .full-table td {
            border: 1px solid #444;
            padding: 10px 12px;
            text-align: center;
        }
        .full-table th {
            background-color: #004d40;
            color: white;
            font-weight: 600;
        }
        .full-table td {
            background-color: rgba(255, 255, 255, 0.02);
            color: inherit;
        }
        .full-table tr:nth-child(even) td {
            background-color: rgba(255, 255, 255, 0.05);
        }
        .full-table tr:hover td {
            background-color: rgba(76, 175, 80, 0.1);
        }
        .full-table td:first-child {
            text-align: left;
            font-weight: 600;
            background-color: rgba(0, 77, 64, 0.2);
        }
        @media (prefers-color-scheme: dark) {
            .full-table th {
                background-color: #0a3d3d;
                color: #ffffff;
            }
            .full-table td {
                color: #f0f0f0;
            }
            .full-table td:first-child {
                background-color: rgba(0, 77, 64, 0.3);
            }
        }
    </style>

    <table class="full-table">
        <tr><th>Description</th><th>Amount</th></tr>
    """

    for field in shared_fields:
        val = row.get(field)
        html += f"<tr><td>{field}</td><td>{fmt(val)}</td></tr>"

    html += """
    </table>
    <table class="full-table" style="margin-top: 0;">
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
