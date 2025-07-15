import streamlit as st
import pandas as pd
from datetime import datetime

# Load Excel files
price_data = pd.read_excel("PriceList.xlsx")
discount_data = pd.read_excel("SchemeList.xlsx")

st.title("🚗 Mahindra Docket Audit Tool")

# --- Inputs ---
model = st.selectbox("Select Model", sorted(price_data["Model"].unique()))
variant_list = price_data[price_data["Model"] == model]["Variant"].unique()
variant = st.selectbox("Select Variant", sorted(variant_list))

fuel_list = price_data[(price_data["Model"] == model) & (price_data["Variant"] == variant)]["Fuel Type"].unique()
fuel_type = st.selectbox("Select Fuel Type", sorted(fuel_list))

booking_date = st.date_input("Select Booking Date", value=datetime.today())
quoted_price = st.number_input("Enter Quoted Price (₹)", min_value=0, step=1000)
discount_applied = st.number_input("Enter Discount Applied (₹)", min_value=0, step=1000)

# --- Audit Button ---
if st.button("🔍 Audit Deal"):
    # Lookup official price
    match_row = price_data[
        (price_data["Model"] == model) &
        (price_data["Variant"] == variant) &
        (price_data["Fuel Type"] == fuel_type)
    ]
    if match_row.empty:
        st.error("No matching model/variant/fuel found in price list.")
    else:
        official_price = match_row["Price"].values[0]

        # Lookup max discount for booking date
        date = pd.to_datetime(booking_date)
        scheme_row = discount_data[
            (discount_data["Model"] == model) &
            (discount_data["Variant"] == variant) &
            (discount_data["Booking Date Start"] <= date) &
            (discount_data["Booking Date End"] >= date)
        ]
        if scheme_row.empty:
            st.warning("⚠️ No scheme found for selected booking date.")
        else:
            max_discount = scheme_row["Max Discount"].values[0]

            # Audit logic
            st.markdown("---")
            st.subheader("📋 Audit Result:")
            issues = []
            if quoted_price != official_price:
                issues.append(f"❌ Price Mismatch: Expected ₹{official_price:,}, Quoted ₹{quoted_price:,}")
            if discount_applied > max_discount:
                issues.append(f"❌ Discount Exceeded: Max ₹{max_discount:,}, Applied ₹{discount_applied:,}")

            if not issues:
                st.success("✅ Deal Approved. All entries are within limits.")
            else:
                for issue in issues:
                    st.error(issue)
