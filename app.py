import streamlit as st
import pandas as pd

# Load Excel file
price_data = pd.read_excel("PV Price List Master D. 08.07.2025.xlsx")

st.title("🚗 Mahindra Vehicle Pricing Viewer")

# --- Step 1: Select Model ---
model = st.selectbox("Select Model", sorted(price_data["Model"].unique()))

# --- Step 2: Select Fuel Type ---
fuel_list = price_data[price_data["Model"] == model]["Fuel Type"].unique()
fuel_type = st.selectbox("Select Fuel Type", sorted(fuel_list))

# --- Step 3: Filtered Variant List Based on Model and Fuel Type ---
filtered_variants = price_data[
    (price_data["Model"] == model) & (price_data["Fuel Type"] == fuel_type)
]
variant_list = filtered_variants["Variant"].unique()
variant = st.selectbox("Select Variant", sorted(variant_list))

# --- Fetch and Display Official Price Data ---
row = price_data[
    (price_data["Model"] == model)
    & (price_data["Variant"] == variant)
    & (price_data["Fuel Type"] == fuel_type)
]

if row.empty:
    st.warning("No matching entry found in the price list.")
else:
    st.markdown("---")
    st.subheader("📋 Official Pricing Details")

    # Display selected row values
    display_fields = [
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

    for field in display_fields:
        value = row.iloc[0].get(field, None)
        if pd.notnull(value):
            st.write(f"**{field}:** ₹{int(value):,}")
        else:
            st.write(f"**{field}:** Not Available")
