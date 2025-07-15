import streamlit as st
import pandas as pd

# Load Excel file
price_data = pd.read_excel("PV Price List Master D. 08.07.2025.xlsx")

st.title("🚗 Mahindra Vehicle Pricing Viewer")

# --- Step 1: Select Model(s) ---
models = st.multiselect("Select Model(s)", sorted(price_data["Model"].unique()))

# --- Step 2: Select Fuel Type(s) ---
fuel_options = price_data[price_data["Model"].isin(models)]["Fuel Type"].unique()
fuel_types = st.multiselect("Select Fuel Type(s)", sorted(fuel_options))

# --- Step 3: Select Variant(s) ---
filtered_variants = price_data[(price_data["Model"].isin(models)) & (price_data["Fuel Type"].isin(fuel_types))]
variant_options = filtered_variants["Variant"].unique()
variants = st.multiselect("Select Variant(s)", sorted(variant_options))

# --- Final Filter ---
selected_rows = price_data[(price_data["Model"].isin(models)) &
                           (price_data["Fuel Type"].isin(fuel_types)) &
                           (price_data["Variant"].isin(variants))]

if selected_rows.empty:
    st.warning("No matching entries found for selected filters.")
else:
    st.markdown("---")
    st.subheader("📊 Price Comparison Table")

    # Columns to display
    display_columns = [
        "Model", "Fuel Type", "Variant",
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

    # Format and show table
    def format_currency(val):
        try:
            return f"₹{int(val):,}"
        except:
            return val

    formatted_df = selected_rows[display_columns].copy()
    for col in display_columns[3:]:  # Format pricing columns
        formatted_df[col] = formatted_df[col].apply(format_currency)

    st.dataframe(formatted_df.reset_index(drop=True), use_container_width=True)
