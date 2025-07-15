import streamlit as st
import pandas as pd

# Load Excel file
price_data = pd.read_excel("PV Price List Master D. 08.07.2025.xlsx")

st.title("🚗 Mahindra Vehicle Pricing Viewer")

# --- Step 1: Select Model ---
model = st.selectbox("Select Model", sorted(price_data["Model"].unique()))

# --- Step 2: Select Fuel Type ---
fuel_options = price_data[price_data["Model"] == model]["Fuel Type"].unique()
fuel_type = st.selectbox("Select Fuel Type", sorted(fuel_options))

# --- Step 3: Select Variant ---
filtered_variants = price_data[(price_data["Model"] == model) & (price_data["Fuel Type"] == fuel_type)]
variant_options = filtered_variants["Variant"].unique()
variant = st.selectbox("Select Variant", sorted(variant_options))

# --- Final Filter ---
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
        "Maxi Care",
        "RTO (W/O HYPO) - Individual",
        "RTO (With HYPO) - Individual",
        "RTO (W/O HYPO) - Corporate",
        "RTO (With HYPO) - Corporate"
    ]

    # Format vertical table
    data = {"Component": [], "Amount": []}
    for field in display_fields:
        value = selected_row.iloc[0].get(field, None)
        amount = f"₹{int(value):,}" if pd.notnull(value) else "Not Available"
        data["Component"].append(field)
        data["Amount"].append(amount)

    st.table(pd.DataFrame(data))
