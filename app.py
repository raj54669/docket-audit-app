import streamlit as st
import pandas as pd
from datetime import datetime

# --- Cached Data Loading with Error Handling ---
@st.cache_data
def load_data():
    try:
        return pd.read_excel("PV Price List Master D. 08.07.2025.xlsx")
    except FileNotFoundError:
        st.error("Error: Pricing file not found. Please ensure 'PV Price List Master D. 08.07.2025.xlsx' exists in the app directory.")
        st.stop()

price_data = load_data()

# --- Main App (Original Visual Design) ---
st.set_page_config(
    page_title="Mahindra Pricing Viewer", 
    layout="centered",
    initial_sidebar_state="auto"
)

st.title("🚗 Mahindra Vehicle Pricing Viewer")

# --- Original 3-Step Selection ---
model = st.selectbox("Select Model", sorted(price_data["Model"].unique()))

fuel_options = price_data[price_data["Model"] == model]["Fuel Type"].unique()
fuel_type = st.selectbox("Select Fuel Type", sorted(fuel_options))

filtered_variants = price_data[(price_data["Model"] == model) & (price_data["Fuel Type"] == fuel_type)]
variant_options = filtered_variants["Variant"].unique()
variant = st.selectbox("Select Variant", sorted(variant_options))

# --- Price Display ---
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
        amount = f"₹{int(value):,}" if pd.notnull(value) else "Not Available"
        pricing_html += f"<li><strong>{field}</strong>: {amount}</li>"
    pricing_html += "</ul>"
    st.markdown(pricing_html, unsafe_allow_html=True)

    # --- RTO Table Styling with Width Fix ---
    html = """
    <style>
        .table-wrapper {
            margin-bottom: 15px;
            max-width: 1100px;
            margin-left: auto;
            margin-right: auto;
        }

        .styled-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 16px;
            line-height: 1.3;
            border: 2px solid black;
        }

        .styled-table th, .styled-table td {
            border: 1px solid black;
            padding: 8px 12px;
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

        @media (prefers-color-scheme: dark) {
            .styled-table {
                border: 2px solid white;
            }

            .styled-table th, .styled-table td {
                border: 1px solid white;
            }

            .styled-table td {
                background-color: #111;
                color: #eee;
            }

            .styled-table td:first-child {
                background-color: #1e1e1e;
                color: white;
            }
        }
    </style>
    """
    st.markdown(html, unsafe_allow_html=True)

    # --- RTO Table Rendering ---
    rto_table = "<div class='table-wrapper'><table class='styled-table'>"
    rto_table += """
        <tr>
            <th>Category</th>
            <th>RTO (W/O HYPO)</th>
            <th>RTO (With HYPO)</th>
        </tr>
    """

    for category in ["Individual", "Corporate"]:
        rto_wo = selected_row.iloc[0].get(f"RTO (W/O HYPO) - {category}", None)
        rto_with = selected_row.iloc[0].get(f"RTO (With HYPO) - {category}", None)
        rto_wo_amt = f"₹{int(rto_wo):,}" if pd.notnull(rto_wo) else "-"
        rto_with_amt = f"₹{int(rto_with):,}" if pd.notnull(rto_with) else "-"
        rto_table += f"<tr><td>{category}</td><td>{rto_wo_amt}</td><td>{rto_with_amt}</td></tr>"

    rto_table += "</table></div>"
    st.markdown(rto_table, unsafe_allow_html=True)
