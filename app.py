import streamlit as st
import pandas as pd
from utils import load_price_data, get_filtered_row, format_currency
from layout import render_pricing_details, render_rto_table

st.set_page_config(page_title="Mahindra Pricing Viewer", layout="centered")
st.title("🚗 Mahindra Vehicle Pricing Viewer")

# Load data with caching
price_data = load_price_data()

# --- Step 1: Select Model ---
model = st.selectbox("Select Model", sorted(price_data["Model"].unique()))

# --- Step 2: Select Fuel Type ---
fuel_options = price_data[price_data["Model"] == model]["Fuel Type"].unique()
fuel_type = st.selectbox("Select Fuel Type", sorted(fuel_options))

# --- Step 3: Select Variant ---
variant_options = price_data[
    (price_data["Model"] == model) & (price_data["Fuel Type"] == fuel_type)
]["Variant"].unique()
variant = st.selectbox("Select Variant", sorted(variant_options))

# --- Final Filter ---
selected_row = get_filtered_row(price_data, model, fuel_type, variant)

if selected_row.empty:
    st.warning("No matching entry found for selected filters.")
else:
    st.markdown("---")
    st.subheader("📋 Vehicle Pricing Details")

    col1, col2 = st.columns([2, 1])
    with col1:
        render_pricing_details(selected_row)
    with col2:
        render_rto_table(selected_row)
