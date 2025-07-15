import streamlit as st
import pandas as pd

# Load Excel file
price_data = pd.read_excel("PV Price List Master D. 08.07.2025.xlsx")

st.set_page_config(page_title="Mahindra Pricing Viewer", layout="centered")
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
        "Maxi Care"
    ]

    pricing_html = "<ul>"
    for field in display_fields:
        value = selected_row.iloc[0].get(field, None)
        amount = f"₹{int(value):,}" if pd.notnull(value) else "Not Available"
        pricing_html += f"<li><strong>{field}</strong>: {amount}</li>"
    pricing_html += "</ul>"
    st.markdown(pricing_html, unsafe_allow_html=True)

    # --- Styled Unified RTO Table ---
    st.markdown("""
        <style>
        .rto-layout {
            width: 100%;
            border-collapse: collapse;
        }
        .rto-layout th, .rto-layout td {
            border: 1px solid #999;
            padding: 8px;
            text-align: center;
        }
        .rto-layout th {
            background-color: #004d40;
            color: white;
        }
        .rto-layout td:first-child {
            font-weight: bold;
            background-color: #e0f2f1;
        }
        </style>
    """, unsafe_allow_html=True)

    rto_table = """
    <table class='rto-layout'>
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

    rto_table += "</table>"
    st.markdown(rto_table, unsafe_allow_html=True)
