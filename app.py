import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import re

# --- Page Configuration ---
st.set_page_config(
    page_title="Mahindra Pricing Viewer",
    layout="wide",
    initial_sidebar_state="auto"
)

# --- Styling and Layout Tweaks ---
st.markdown("""
    <style>
    .block-container {
        padding-top: 0.25rem !important;
        padding-bottom: 0.25rem !important;
        max-width: 75vw;
        width: 100%;
        margin: auto;
    }
    header[data-testid="stHeader"] {
        height: 0rem;
        visibility: hidden;
    }

    .table-wrapper { margin-bottom: 15px; padding: 0; }
    .styled-table {
        width: 100%;
        max-width: 100%;
        border-collapse: collapse;
        font-size: 14px;
        line-height: 1.2;
        border: 2px solid black;
        table-layout: fixed;
        word-wrap: break-word;
    }
    .styled-table th, .styled-table td {
        border: 1px solid black;
        padding: 6px 8px;
        text-align: center;
    }
    .styled-table th {
        background-color: #004d40;
        color: white;
        font-weight: bold;
    }
    .styled-table td:first-child {
        text-align: left;
        font-weight: 600;
        background-color: #f7f7f7;
    }
    @media (prefers-color-scheme: dark) {
        .styled-table { border: 2px solid white; }
        .styled-table th, .styled-table td { border: 1px solid white; }
        .styled-table td { background-color: #111; color: #eee; }
        .styled-table td:first-child { background-color: #1e1e1e; color: white; }
    }
    .table-wrapper + .table-wrapper { margin-top: -8px; }

    .row-widget.stSelectbox > div {
        width: 100% !important;
        max-width: 100% !important;
    }

    .stSelectbox label {
        font-weight: 600;
    }

    .stColumns > div {
        padding-right: 8px !important;
    }

    h1 { font-size: 32px !important; }
    h2 { font-size: 20px !important; }
    h3 { font-size: 18px !important; }
    </style>
""", unsafe_allow_html=True)

# --- Constants ---
FILE_PATH = "PV Price List Master D. 08.07.2025.xlsx"
SHARED_FIELDS = [
    "Ex-Showroom Price", "TCS 1%", "Insurance 1 Yr OD + 3 Yr TP + Zero Dep.",
    "Accessories Kit", "SMC", "Extended Warranty", "Maxi Care", "RSA (1 Year)", "Fastag"
]
GROUPED_FIELDS = [
    "RTO (W/O HYPO)", "RTO (With HYPO)",
    "On Road Price (W/O HYPO)", "On Road Price (With HYPO)"
]
GROUP_KEYS = {
    "RTO (W/O HYPO)": ("RTO (W/O HYPO) - Individual", "RTO (W/O HYPO) - Corporate"),
    "RTO (With HYPO)": ("RTO (With HYPO) - Individual", "RTO (With HYPO) - Corporate"),
    "On Road Price (W/O HYPO)": ("On Road Price (W/O HYPO) - Individual", "On Road Price (W/O HYPO) - Corporate"),
    "On Road Price (With HYPO)": ("On Road Price (With HYPO) - Individual", "On Road Price (With HYPO) - Corporate"),
}

# --- Helper Functions ---
@st.cache_data(show_spinner=False)
def load_data(file_path: str) -> pd.DataFrame:
    if not os.path.exists(file_path):
        st.error("❌ Pricing file not found.")
        st.stop()
    try:
        return pd.read_excel(file_path)
    except Exception as e:
        st.error(f"❌ Failed to load Excel file: {e}")
        st.stop()

def format_indian_currency(value) -> str:
    if pd.isnull(value):
        return "<i style='color:gray;'>N/A</i>"
    try:
        value = float(value)
        is_negative = value < 0
        value = abs(value)
        s = str(int(value))
        last_three, other = s[-3:], s[:-3]
        if other:
            other = re.sub(r'(\d)(?=(\d{2})+$)', r'\1,', other)
            formatted = f"{other},{last_three}"
        else:
            formatted = last_three
        result = f"₹{formatted}"
        return f"<b>{'-' if is_negative else ''}{result}</b>"
    except Exception:
        return "<i style='color:red;'>Invalid</i>"

def render_shared_table(row: pd.Series, fields: list[str]) -> str:
    rows = "\n".join(
        f"<tr><td>{field}</td><td>{format_indian_currency(row.get(field))}</td></tr>"
        for field in fields
    )
    return f"""
    <div class="table-wrapper">
    <table class="styled-table">
        <tr><th>Description</th><th>Amount</th></tr>
        {rows}
    </table></div>
    """

def render_registration_table(row: pd.Series, groups: list[str], keys: dict) -> str:
    rows = "\n".join(
        f"<tr><td>{field}</td><td>{format_indian_currency(row.get(keys[field][0]))}</td><td>{format_indian_currency(row.get(keys[field][1]))}</td></tr>"
        for field in groups
    )
    return f"""
    <div class="table-wrapper">
    <table class="styled-table">
        <tr><th>Registration</th><th>Individual</th><th>Corporate</th></tr>
        {rows}
    </table></div>
    """

# --- App Title ---
st.title("🚗 Mahindra Vehicle Pricing Viewer")

# --- Load Data ---
price_data = load_data(FILE_PATH)

# --- Timestamp Display ---
try:
    ist_time = datetime.fromtimestamp(os.path.getmtime(FILE_PATH)) + timedelta(hours=5, minutes=30)
    st.caption(f"📅 Data last updated on: {ist_time.strftime('%d-%b-%Y %I:%M %p')} (IST)")
except Exception:
    st.caption("📅 Last update timestamp not available.")

# --- Dropdown Section: 3 Equal Columns ---
models = sorted(price_data["Model"].dropna().unique())
if not models:
    st.error("❌ No models found in data.")
    st.stop()

col1, col2, col3 = st.columns([3.2, 1.5, 4.5])

with col1:
    model = st.selectbox("🚙 Model", models)

fuel_df = price_data[price_data["Model"] == model]
fuel_types = sorted(fuel_df["Fuel Type"].dropna().unique())
if not fuel_types:
    st.error("❌ No fuel types found for selected model.")
    st.stop()

with col2:
    fuel_type = st.selectbox("⛽ Fuel", fuel_types)

variant_df = fuel_df[fuel_df["Fuel Type"] == fuel_type]
variant_options = sorted(variant_df["Variant"].dropna().unique())
if not variant_options:
    st.error("❌ No variants available for selected fuel type.")
    st.stop()

with col3:
    variant = st.selectbox("🎯 Variant", variant_options)

selected_row = variant_df[variant_df["Variant"] == variant]
if selected_row.empty:
    st.warning("⚠️ No data found for selected filters.")
    st.stop()

row = selected_row.iloc[0]

# --- Display Summary ---
st.markdown(f"### 🚙 {model} - {fuel_type} - {variant}")

# --- Display Tables ---
st.subheader("📋 Vehicle Pricing Details")
st.markdown(render_shared_table(row, SHARED_FIELDS), unsafe_allow_html=True)
st.markdown(render_registration_table(row, GROUPED_FIELDS, GROUP_KEYS), unsafe_allow_html=True)
