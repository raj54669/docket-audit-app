import streamlit as st
import pandas as pd
from datetime import datetime

# Load Excel file
price_data = pd.read_excel("PV Price List Master D. 08.07.2025.xlsx")

st.title("🚗 Mahindra Docket Audit Tool")

# --- Inputs ---
model = st.selectbox("Select Model", sorted(price_data["Model"].unique()))
variant_list = price_data[price_data["Model"] == model]["Variant"].unique()
variant = st.selectbox("Select Variant", sorted(variant_list))

fuel_list = price_data[(price_data["Model"] == model) & (price_data["Variant"] == variant)]["Fuel Type"].unique()
fuel_type = st.selectbox("Select Fuel Type", sorted(fuel_list))

# Filter the row for this selection
row = price_data[(price_data["Model"] == model) &
                 (price_data["Variant"] == variant) &
                 (price_data["Fuel Type"] == fuel_type)]

if row.empty:
    st.error("No matching model/variant/fuel type found in price list.")
else:
    st.markdown("---")
    st.subheader("Enter Quoted Price Components")

    # Define expected fields from the Excel
    components = [
        "Ex-Showroom Price",
        "TCS 1%",
        "Insurance 1 Yr OD + 3 Yr TP + Zero Dep.",
        "Accessories Kit",
        "SMC",
        "Extended Warranty",
        "Maxi Care",
        "RTO (W/O HYPO) - Individual",
        "RTO (With HYPO) - Individual",
        "RTO (W/O HYPO) - Corporate",
        "RTO (With HYPO) - Corporate"
    ]

    quoted_values = {}
    for comp in components:
        quoted_values[comp] = st.number_input(f"{comp} (₹)", min_value=0, step=500)

    if st.button("🔍 Audit Deal"):
        st.markdown("---")
        st.subheader("📋 Audit Result:")
        official_values = row.iloc[0]
        mismatches = []

        for comp in components:
            official = official_values[comp] if comp in official_values else None
            quoted = quoted_values[comp]
            if pd.notnull(official):
                if int(official) != int(quoted):
                    mismatches.append(f"❌ {comp}: Expected ₹{official:,}, Quoted ₹{quoted:,}")

        if mismatches:
            for msg in mismatches:
                st.error(msg)
        else:
            st.success("✅ All price components match official values. Deal Approved.")
