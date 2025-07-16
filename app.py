import streamlit as st
import pandas as pd
from datetime import datetime
import re

# --- Page Configuration ---
st.set_page_config(
    page_title="Mahindra Pricing Viewer",
    layout="centered",
    initial_sidebar_state="auto"
)

# --- Load Excel Data from GitHub ---
@st.cache_data(show_spinner=False)
def load_data_from_github():
    url = "https://raw.githubusercontent.com/your-username/your-repo/main/PV%20Price%20List%20Master%20D.%2008.07.2025.xlsx"
    try:
        return pd.read_excel(url)
    except Exception as e:
        st.error(f"❌ Failed to load Excel file from GitHub: {e}")
        st.stop()

price_data = load_data_from_github()

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
        decimal_part = f"{value:.2f}".split('.')[-1]
        result = f"₹{formatted}.{decimal_part}"
        return f"<b>{'-' if is_negative else ''}{result}</b>"
    except Exception:
        return "<i style='color:red;'>Invalid</i>"

# --- Table Generators ---
def render_shared_table(row, fields):
    html = """
    <div class="table-wrapper">
    <table class="styled-table">
        <tr><th>Description</th><th>Amount</th></tr>
    """
    for field in fields:
        value = row.get(field, None)
        html += f"<tr><td>{field}</td><td>{format_indian_currency(value)}</td></tr>"
    html += "</table></div>"
    return html

def render_registration_table(row, groups, keys):
    html = """
    <div class="table-wrapper">
    <table class="styled-table">
        <tr><th>Registration</th><th>Individual</th><th>Corporate</th></tr>
    """
    for field in groups:
        ind_key, corp_key = keys.get(field, ("", ""))
        html += f"<tr><td>{field}</td><td>{format_indian_currency(row.get(ind_key))}</td><td>{format_indian_currency(row.get(corp_key))}</td></tr>"
    html += "</table></div>"
    return html

# --- Theme Styling (light/dark responsive) ---
st.markdown("""
<style>
/* Table Styling */
.table-wrapper { margin-bottom: 15px; padding: 0; }
.styled-table {
    width: 100%; border-collapse: collapse;
    font-size: 16px; line-height: 1.2; border: 2px solid black;
}
.styled-table th, .styled-table td {
    border: 1px solid black; padding: 8px 10px; text-align: center;
}
.styled-table th {
    background-color: #004d40; color: white; font-weight: bold;
}
.styled-table td:first-child {
    text-align: left; font-weight: 600; background-color: #f7f7f7;
}

/* Light Mode */
@media (prefers-color-scheme: light) {
    body, .stApp {
        background-color: #ffffff;
        color: #000000;
        font-family: 'Segoe UI', sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #004d40;
        color: white;
    }
    h1, h2, label {
        color: #004d40;
    }
}

/* Dark Mode */
@media (prefers-color-scheme: dark) {
    body, .stApp {
        background-color: #0d0d0d;
        color: #e0e0e0;
    }
    section[data-testid="stSidebar"] {
        background-color: #00251a;
    }
    h1, h2, label {
        color: #80cbc4;
    }
    .styled-table {
        border: 2px solid white;
    }
    .styled-table th, .styled-table td {
        border: 1px solid white;
    }
    .styled-table td {
        background-color: #111;
        color: #eee;
    }
    .styled-table td:first-child {
        background-color: #1e1e1e;
        color: white;
    }
}
</style>
""", unsafe_allow_html=True)

# --- Title ---
st.title("🚗 Mahindra Vehicle Pricing Viewer")

# --- Dropdown Filters ---
models = sorted(price_data["Model"].dropna().unique())
if not models:
    st.error("❌ No models found in data.")
    st.stop()

model = st.selectbox("🚘 Select Model", models)

fuel_df = price_data[price_data["Model"] == model]
fuel_types = sorted(fuel_df["Fuel Type"].dropna().unique())
if not fuel_types:
    st.error("❌ No fuel types found for selected model.")
    st.stop()

fuel_type = st.selectbox("⛽ Select Fuel Type", fuel_types)

variant_df = fuel_df[fuel_df["Fuel Type"] == fuel_type]
variant_options = sorted(variant_df["Variant"].dropna().unique())
if not variant_options:
    st.error("❌ No variants available for selected fuel type.")
    st.stop()

variant = st.selectbox("🎯 Select Variant", variant_options)

selected_row = variant_df[variant_df["Variant"] == variant]
if selected_row.empty:
    st.warning("⚠️ No data found for selected filters.")
    st.stop()

row = selected_row.iloc[0]

# --- Field Configs ---
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

# --- Output Tables ---
st.subheader("📋 Vehicle Pricing Details")
st.markdown(render_shared_table(row, shared_fields), unsafe_allow_html=True)
st.markdown(render_registration_table(row, grouped_fields, group_keys), unsafe_allow_html=True)
