import streamlit as st
import pandas as pd
from datetime import datetime

@st.cache_data
def load_data():
    try:
        return pd.read_excel("PV Price List Master D. 08.07.2025.xlsx")
    except FileNotFoundError:
        st.error("Error: Pricing file not found. Please ensure the Excel file exists.")
        st.stop()

price_data = load_data()

st.set_page_config(
    page_title="Mahindra Pricing Viewer",
    layout="centered",
    initial_sidebar_state="auto"
)

st.title("🚗 Mahindra Vehicle Pricing Viewer")

# Vehicle Selection
model = st.selectbox("Select Model", sorted(price_data["Model"].unique()))
fuel_type = st.selectbox("Select Fuel Type", 
                        sorted(price_data[price_data["Model"] == model]["Fuel Type"].unique()))
variant = st.selectbox("Select Variant", 
                      sorted(price_data[(price_data["Model"] == model) & 
                                      (price_data["Fuel Type"] == fuel_type)]["Variant"].unique()))

selected_row = price_data[(price_data["Model"] == model) &
                         (price_data["Fuel Type"] == fuel_type) &
                         (price_data["Variant"] == variant)]

if selected_row.empty:
    st.warning("No matching entry found for selected filters.")
else:
    st.markdown("---")
    st.subheader("📋 Vehicle Pricing Details")
    
    # Unified Pricing Table
    st.markdown("""
    <style>
    .unified-table {
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
        font-family: Arial, sans-serif;
    }
    .unified-table th {
        background-color: #004d40;
        color: white;
        padding: 10px;
        text-align: left;
    }
    .unified-table td {
        padding: 10px;
        border-bottom: 1px solid #ddd;
    }
    .unified-table tr:nth-child(even) {
        background-color: #e0f2f1;
    }
    .price-value {
        font-weight: bold;
        text-align: right;
    }
    </style>

    <table class='unified-table'>
        <tr>
            <th>Item</th>
            <th>Amount (₹)</th>
        </tr>
        <tr>
            <td><strong>Ex-Showroom Price</strong></td>
            <td class='price-value'>₹{ex_showroom:,}</td>
        </tr>
        <tr>
            <td><strong>TCS 1%</strong></td>
            <td class='price-value'>₹{tcs:,}</td>
        </tr>
        <tr>
            <td><strong>Insurance</strong></td>
            <td class='price-value'>₹{insurance:,}</td>
        </tr>
        <tr>
            <td><strong>Accessories Kit</strong></td>
            <td class='price-value'>₹{accessories:,}</td>
        </tr>
        <tr>
            <td><strong>SMC</strong></td>
            <td class='price-value'>₹{smc:,}</td>
        </tr>
        <tr>
            <td><strong>Extended Warranty</strong></td>
            <td class='price-value'>₹{warranty:,}</td>
        </tr>
        <tr>
            <td><strong>Maxi Care</strong></td>
            <td class='price-value'>₹{maxi_care:,}</td>
        </tr>
    </table>
    """.format(
        ex_showroom=int(selected_row["Ex-Showroom Price"].iloc[0]),
        tcs=int(selected_row["TCS 1%"].iloc[0]),
        insurance=int(selected_row["Insurance 1 Yr OD + 3 Yr TP + Zero Dep."].iloc[0]),
        accessories=int(selected_row["Accessories Kit"].iloc[0]),
        smc=int(selected_row["SMC"].iloc[0]),
        warranty=int(selected_row["Extended Warranty"].iloc[0]),
        maxi_care=int(selected_row["Maxi Care"].iloc[0])
    ), unsafe_allow_html=True)

    # RTO Table (maintaining original style)
    st.markdown("---")
    st.subheader("🚦 RTO Charges")
    
    st.markdown("""
    <style>
    .rto-table {
        width: 100%;
        border-collapse: collapse;
    }
    .rto-table th, .rto-table td {
        border: 1px solid #999;
        padding: 8px;
        text-align: center;
    }
    .rto-table th {
        background-color: #004d40;
        color: white;
    }
    .rto-table td:first-child {
        font-weight: bold;
        background-color: #e0f2f1;
    }
    </style>

    <table class='rto-table'>
        <tr>
            <th>Category</th>
            <th>RTO (W/O HYPO)</th>
            <th>RTO (With HYPO)</th>
        </tr>
        <tr>
            <td>Individual</td>
            <td>₹{rto_wo_ind:,}</td>
            <td>₹{rto_with_ind:,}</td>
        </tr>
        <tr>
            <td>Corporate</td>
            <td>₹{rto_wo_corp:,}</td>
            <td>₹{rto_with_corp:,}</td>
        </tr>
    </table>
    """.format(
        rto_wo_ind=int(selected_row["RTO (W/O HYPO) - Individual"].iloc[0]),
        rto_with_ind=int(selected_row["RTO (With HYPO) - Individual"].iloc[0]),
        rto_wo_corp=int(selected_row["RTO (W/O HYPO) - Corporate"].iloc[0]),
        rto_with_corp=int(selected_row["RTO (With HYPO) - Corporate"].iloc[0])
    ), unsafe_allow_html=True)
