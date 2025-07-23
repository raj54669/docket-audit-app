import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import re
from github import Github

# --- Page Configuration ---
st.set_page_config(
    page_title="Mahindra Pricing Viewer",
    layout="centered",
    initial_sidebar_state="auto"
)

# --- Global Styling ---
st.markdown("""
    <style>
    :root {
        --title-size: 40px;
        --subtitle-size: 18px;
        --caption-size: 16px;
        --label-size: 14px;
        --select-font-size: 15px;
        --table-font-size: 14px;
        --variant-title-size: 20px;
    }

    .block-container {
        padding-top: 0rem;
    }
    header {visibility: hidden;}

    h1 { font-size: var(--title-size) !important; }
    h2 { font-size: var(--subtitle-size) !important; }
    h3 { font-size: var(--variant-title-size) !important; }
    .stCaption { font-size: var(--caption-size) !important; }

    .stSelectbox label {
        font-size: var(--label-size) !important;
        font-weight: 600 !important;
    }

    .stSelectbox div[data-baseweb="select"] > div {
        font-size: var(--select-font-size) !important;
        font-weight: bold !important;
        padding-top: 2px !important;
        padding-bottom: 2px !important;
        line-height: 1 !important;
        min-height: 24px !important;
    }

    .stSelectbox div[data-baseweb="select"] {
        align-items: center !important;
        height: 28px !important;
    }

    .stSelectbox [data-baseweb="menu"] > div {
        padding-top: 2px !important;
        padding-bottom: 2px !important;
    }

    .stSelectbox [data-baseweb="option"] {
        padding: 4px 10px !important;
        font-size: var(--select-font-size) !important;
        font-weight: 500 !important;
        line-height: 1.2 !important;
        min-height: 28px !important;
    }

    .stSelectbox [data-baseweb="option"]:hover {
        background-color: #f0f0f0 !important;
        font-weight: 600 !important;
    }

    .styled-table { font-size: var(--table-font-size) !important; }
    </style>
""", unsafe_allow_html=True)

# --- GitHub Setup ---
@st.cache_resource
def connect_github():
    access_token = st.secrets["github"]["access_token"]
    repo_name = "raj54669/docket-audit-app"
    g = Github(access_token)
    repo = g.get_repo(repo_name)
    return repo

# --- Utility: Get recent pricing files ---
def get_recent_files(repo, folder="Data/Price_List"):
    contents = repo.get_contents(folder)
    files = [f for f in contents if f.name.endswith(".xlsx") and " D. " in f.name]
    sorted_files = sorted(
        files,
        key=lambda f: datetime.strptime(f.name.split(" D. ")[-1].replace(".xlsx", ""), "%d.%m.%Y"),
        reverse=True
    )
    return sorted_files[:5]

# --- Load Excel from GitHub ---
@st.cache_data(show_spinner=False)
def load_excel_file(file_content):
    return pd.read_excel(file_content)

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

# --- Table Styling ---
st.markdown("""
    <style>
    .table-wrapper { margin-bottom: 15px; padding: 0; }
    .styled-table {
        width: 100%; border-collapse: collapse; table-layout: fixed;
        font-size: 14px; line-height: 1; border: 2px solid black;
    }
    .styled-table th, .styled-table td {
        border: 1px solid black; padding: 4px 10px; text-align: center; line-height: 1;
    }
    .styled-table th:nth-child(1), .styled-table td:nth-child(1) {
        width: 60%;
    }
    .styled-table th:nth-child(2), .styled-table td:nth-child(2),
    .styled-table th:nth-child(3), .styled-table td:nth-child(3) {
        width: 20%;
    }
    .styled-table th { background-color: #004d40; color: white; font-weight: bold; }
    .styled-table td:first-child {
        text-align: left; font-weight: 600; background-color: #f7f7f7;
    }
    @media (prefers-color-scheme: dark) {
        .styled-table { border: 2px solid white; }
        .styled-table th, .styled-table td { border: 1px solid white; }
        .styled-table td { background-color: #111; color: #eee; }
        .styled-table td:first-child { background-color: #1e1e1e; color: white; }
    }
    </style>
""", unsafe_allow_html=True)

# --- Title ---
st.title("🚗 Mahindra Vehicle Pricing Viewer")

# --- Load from GitHub ---
repo = connect_github()
recent_files = get_recent_files(repo)
file_names = [f.name for f in recent_files]
default_index = 0
selected_file_name = st.selectbox("Select Price List File", file_names, index=default_index)
selected_file = next(f for f in recent_files if f.name == selected_file_name)
excel_bytes = selected_file.decoded_content
price_data = load_excel_file(excel_bytes)

# --- Timestamp ---
try:
    ist_time = datetime.strptime(selected_file.name.split(" D. ")[-1].replace(".xlsx", ""), "%d.%m.%Y")
    st.caption(f"📅 Data date: {ist_time.strftime('%d-%b-%Y')} (based on filename)")
except Exception:
    st.caption("📅 Date unavailable from filename.")

# --- Dropdowns ---
models = sorted(price_data["Model"].dropna().unique())
if not models:
    st.error("❌ No models found in data.")
    st.stop()

col1, col2 = st.columns([2, 1])
with col1:
    model = st.selectbox("🚘 Select Model", models)

fuel_df = price_data[price_data["Model"] == model]
fuel_types = sorted(fuel_df["Fuel Type"].dropna().unique())
if not fuel_types:
    st.error("❌ No fuel types found for selected model.")
    st.stop()

with col2:
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
