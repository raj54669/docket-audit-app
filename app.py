import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import re

# --- Page Configuration ---
st.set_page_config(
    page_title="Mahindra Pricing Viewer",
    layout="centered",
    initial_sidebar_state="auto"
)

# --- Global Styling ---
st.markdown("""<style> ... </style>""", unsafe_allow_html=True)  # KEEP your original style block

# --- Find Last 5 Files Based on Date in Filename ---
def extract_date(filename):
    match = re.search(r'D\.\s*(\d{2})\.(\d{2})\.(\d{4})', filename)
    if match:
        day, month, year = match.groups()
        return datetime(int(year), int(month), int(day))
    return datetime.min

@st.cache_data(show_spinner=False)
def get_recent_files():
    all_files = [
        f for f in os.listdir() if f.startswith("PV Price List Master D.") and f.endswith(".xlsx")
    ]
    dated_files = [(f, extract_date(f)) for f in all_files]
    dated_files.sort(key=lambda x: x[1], reverse=True)
    return [f[0] for f in dated_files[:5]]

recent_files = get_recent_files()
if not recent_files:
    st.error("❌ No price list files found.")
    st.stop()

# --- File Selection Dropdown ---
selected_file = st.selectbox("📂 Select Price List File", recent_files, index=0)

# --- Load Excel Data ---
@st.cache_data(show_spinner=False)
def load_data(file_path):
    try:
        return pd.read_excel(file_path)
    except Exception as e:
        st.error(f"❌ Failed to load Excel file: {e}")
        st.stop()

price_data = load_data(selected_file)

# --- Persist Selections Across File Switch ---
stored_model = st.session_state.get("model", "")
stored_fuel = st.session_state.get("fuel", "")
stored_variant = st.session_state.get("variant", "")

# --- Currency Formatter (Indian style) ---
def format_indian_currency(value):
    if pd.isnull(value):
        return "<i style='color:gray;'>N/A</i>"
    try:
        value = float(value)
        is_negative = value < 0
        value = abs(value)
        s = f"{int(value)}"
        last_three = s[-3:]
        other = s[:-3]
        if other:
            other = re.sub(r'(\d)(?=(\d{2})+$)', r'\1,', other)
            formatted = f"{other},{last_three}"
        else:
            formatted = last_three
        result = f"₹{formatted}"
        return f"<b>{'-' if is_negative else ''}{result}</b>"
    except Exception:
        return "<i style='color:red;'>Invalid</i>"

# --- Unified Table Renderer ---
def render_combined_table(row, shared_fields, grouped_fields, group_keys):
    html = """
    <div class="table-wrapper">
    <table class="styled-table">
        <tr><th>Description</th><th>Individual</th><th>Corporate</th></tr>
    """
    for field in shared_fields:
        ind_val = format_indian_currency(row.get(field))
        corp_val = format_indian_currency(row.get(field))
        html += f"<tr><td>{field}</td><td>{ind_val}</td><td>{corp_val}</td></tr>"
    for field in grouped_fields:
        ind_key, corp_key = group_keys.get(field, ("", ""))
        ind_val = format_indian_currency(row.get(ind_key))
        corp_val = format_indian_currency(row.get(corp_key))
        highlight = " style='background-color:#fff3cd;font-weight:bold;'" if field.startswith("On Road Price") else ""
        html += f"<tr{highlight}><td>{field}</td><td>{ind_val}</td><td>{corp_val}</td></tr>"
    html += "</table></div>"
    return html

# --- Timestamp Display ---
try:
    ist_time = datetime.fromtimestamp(os.path.getmtime(selected_file)) + timedelta(hours=5, minutes=30)
    st.caption(f"📅 Data last updated on: {ist_time.strftime('%d-%b-%Y %I:%M %p')} (IST)")
except Exception:
    st.caption("📅 Last update timestamp not available.")

# --- Dropdowns ---
models = sorted(price_data["Model"].dropna().unique())
if not models:
    st.error("❌ No models found in data.")
    st.stop()

default_model = stored_model if stored_model in models else models[0]
model = st.selectbox("🚘 Select Model", models, index=models.index(default_model))

fuel_df = price_data[price_data["Model"] == model]
fuel_types = sorted(fuel_df["Fuel Type"].dropna().unique())
if not fuel_types:
    st.error("❌ No fuel types found for selected model.")
    st.stop()

default_fuel = stored_fuel if stored_fuel in fuel_types else fuel_types[0]
fuel_type = st.selectbox("⛽ Select Fuel Type", fuel_types, index=fuel_types.index(default_fuel))

variant_df = fuel_df[fuel_df["Fuel Type"] == fuel_type]
variant_options = sorted(variant_df["Variant"].dropna().unique())
if not variant_options:
    st.error("❌ No variants available for selected fuel type.")
    st.stop()

default_variant = stored_variant if stored_variant in variant_options else variant_options[0]
variant = st.selectbox("🎯 Select Variant", variant_options, index=variant_options.index(default_variant))

# Save selections
st.session_state["model"] = model
st.session_state["fuel"] = fuel_type
st.session_state["variant"] = variant

selected_row = variant_df[variant_df["Variant"] == variant]
if selected_row.empty:
    st.warning("⚠️ No data found for selected filters.")
    st.stop()

row = selected_row.iloc[0]

shared_fields = [
    "Ex-Showroom Price", "TCS 1%", "Insurance 1 Yr OD + 3 Yr TP + Zero Dep.",
    "Accessories Kit", "SMC", "Extended Warranty", "Maxi Care", "RSA (1 Year)", "Fastag"
]

grouped_fields = [
    "RTO (W/O HYPO)", "RTO (With HYPO)",
    "On Road Price (W/O HYPO)", "On Road Price (With HYPO)"
]

group_keys = {
    "RTO (W/O HYPO)": ("RTO (W/O HYPO) - Individual", "RTO (W/O HYPO) - Corporate"),
    "RTO (With HYPO)": ("RTO (With HYPO) - Individual", "RTO (With HYPO) - Corporate"),
    "On Road Price (W/O HYPO)": ("On Road Price (W/O HYPO) - Individual", "On Road Price (W/O HYPO) - Corporate"),
    "On Road Price (With HYPO)": ("On Road Price (With HYPO) - Individual", "On Road Price (With HYPO) - Corporate"),
}

st.markdown(f"### 🚙 {model} - {fuel_type} - {variant}")
st.subheader("📋 Vehicle Pricing Details")
st.markdown(render_combined_table(row, shared_fields, grouped_fields, group_keys), unsafe_allow_html=True)
