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
    
    # Create unified table
    st.markdown("""
    <style>
    .pricing-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
    }
    .pricing-table th, .pricing-table td {
        border: 1px solid #999;
        padding: 10px;
        text-align: center;
    }
    .pricing-table th {
        background-color: #004d40;
        color: white;
    }
    .pricing-table tr:nth-child(even) {
        background-color: #e0f2f1;
    }
    .price-value {
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main Pricing Table
    pricing_table = """
    <table class='pricing-table'>
        <tr>
            <th>Item</th>
            <th>Amount (₹)</th>
        </tr>
    """
    
    pricing_items = [
        ("Ex-Showroom Price", "Ex-Showroom Price"),
        ("TCS 1%", "TCS 1%"),
        ("Insurance", "Insurance 1 Yr OD + 3 Yr TP + Zero Dep."),
        ("Accessories Kit", "Accessories Kit"),
        ("SMC", "SMC"),
        ("Extended Warranty", "Extended Warranty"),
        ("Maxi Care", "Maxi Care")
    ]
    
    for display_name, field_name in pricing_items:
        value = selected_row.iloc[0].get(field_name, None)
        amount = f"{int(value):,}" if pd.notnull(value) else "-"
        pricing_table += f"""
        <tr>
            <td><strong>{display_name}</strong></td>
            <td class='price-value'>₹{amount}</td>
        </tr>
        """
    
    pricing_table += "</table>"
    st.markdown(pricing_table, unsafe_allow_html=True)
    
    # RTO Table (same style)
    st.markdown("---")
    st.subheader("🚦 RTO Charges")
    
    rto_table = """
    <table class='pricing-table'>
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
        
        rto_table += f"""
        <tr>
            <td>{category}</td>
            <td class='price-value'>{rto_wo_amt}</td>
            <td class='price-value'>{rto_with_amt}</td>
        </tr>
        """
    
    rto_table += "</table>"
    st.markdown(rto_table, unsafe_allow_html=True)
