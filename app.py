import streamlit as st
import pandas as pd
from datetime import datetime

# --- Data Loading with Caching & Error Handling ---
@st.cache_data
def load_data():
    try:
        data = pd.read_excel("PV Price List Master D. 08.07.2025.xlsx")
        data["Last_Updated"] = datetime.now().strftime("%d-%m-%Y %H:%M")
        return data
    except FileNotFoundError:
        st.error("❌ Error: Pricing file not found. Please ensure 'PV Price List Master D. 08.07.2025.xlsx' exists.")
        st.stop()

price_data = load_data()

# --- Main App UI ---
st.set_page_config(
    page_title="Mahindra Pricing Viewer",
    layout="centered",
    initial_sidebar_state="auto"  # Enables system dark/light mode
)

st.title("🚗 Mahindra Vehicle Pricing Viewer")
st.caption(f"Last updated: {price_data['Last_Updated'].iloc[0]}")

# --- Vehicle Selection ---
model = st.selectbox("Select Model", sorted(price_data["Model"].unique()))
fuel_type = st.selectbox(
    "Select Fuel Type",
    sorted(price_data[price_data["Model"] == model]["Fuel Type"].unique())
)
variant = st.selectbox(
    "Select Variant",
    sorted(price_data[
        (price_data["Model"] == model) &
        (price_data["Fuel Type"] == fuel_type)
    ]["Variant"].unique())
)

# --- Price Display ---
selected_row = price_data[
    (price_data["Model"] == model) &
    (price_data["Fuel Type"] == fuel_type) &
    (price_data["Variant"] == variant)
]

if not selected_row.empty:
    st.markdown("---")
    st.subheader("📋 Pricing Details")
    
    # Core pricing fields
    st.write(f"**Ex-Showroom Price:** ₹{selected_row['Ex-Showroom Price'].iloc[0]:,}")
    st.write(f"**Insurance:** ₹{selected_row['Insurance 1 Yr OD + 3 Yr TP + Zero Dep.'].iloc[0]:,}")
    st.write(f"**Extended Warranty:** ₹{selected_row['Extended Warranty'].iloc[0]:,}")
    
    # RTO Table (existing feature)
    st.markdown("---")
    st.subheader("🚦 RTO Charges")
    rto_data = {
        "Category": ["Individual", "Corporate"],
        "Without Hypothecation": [
            f"₹{selected_row['RTO (W/O HYPO) - Individual'].iloc[0]:,}",
            f"₹{selected_row['RTO (W/O HYPO) - Corporate'].iloc[0]:,}"
        ],
        "With Hypothecation": [
            f"₹{selected_row['RTO (With HYPO) - Individual'].iloc[0]:,}",
            f"₹{selected_row['RTO (With HYPO) - Corporate'].iloc[0]:,}"
        ]
    }
    st.table(pd.DataFrame(rto_data))
    
else:
    st.warning("⚠️ No pricing data found for the selected variant.")
