# streamlit_app.py (Final Full Version with Timestamp Removed)
import streamlit as st
import pandas as pd
import os
import re
import base64
import requests
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Mahindra Pricing Viewer",
    layout="centered",
    initial_sidebar_state="auto"
)

# --- Constants ---
DATA_DIR = "Data/Price_List"
FILE_PATTERN = r"PV Price List Master D\. (\d{2})\.(\d{2})\.(\d{4})\.xlsx"

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
.block-container { padding-top: 0rem; }
header {visibility: hidden;}
h1 { font-size: var(--title-size) !important; }
h2 { font-size: var(--subtitle-size) !important; }
h3 { font-size: var(--variant-title-size) !important; }
.stCaption { display: none !important; }
.stSelectbox label { font-size: var(--label-size) !important; font-weight: 600 !important; }
.stSelectbox div[data-baseweb="select"] > div {
    font-size: var(--select-font-size) !important;
    font-weight: bold !important;
    padding-top: 2px !important;
    padding-bottom: 2px !important;
    line-height: 1 !important;
    min-height: 24px !important;
}
.stSelectbox div[data-baseweb="select"] { align-items: center !important; height: 28px !important; }
.stSelectbox [data-baseweb="menu"] > div { padding-top: 2px !important; padding-bottom: 2px !important; }
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
.table-wrapper { margin-bottom: 15px; padding: 0; }
.styled-table {
    width: 100%; border-collapse: collapse; table-layout: fixed;
    font-size: var(--table-font-size); line-height: 1; border: 2px solid black;
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

# --- File Listing ---
def extract_date_from_filename(filename):
    match = re.match(FILE_PATTERN, filename)
    if match:
        return datetime.strptime(".".join(match.groups()), "%d.%m.%Y")
    return None

def list_recent_files():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    all_files = os.listdir(DATA_DIR)
    valid = [(f, extract_date_from_filename(f)) for f in all_files if extract_date_from_filename(f)]
    return sorted(valid, key=lambda x: x[1], reverse=True)[:5]

files = list_recent_files()
if not files:
    st.error("❌ No valid Excel files found")
    st.stop()

file_labels = [f"{name} ({dt.strftime('%d-%b-%Y')})" for name, dt in files]
file_map = {label: name for label, (name, _) in zip(file_labels, files)}

selected_label = st.selectbox("📅 Select Excel File", file_labels, key="main_excel_file")
selected_path = os.path.join(DATA_DIR, file_map[selected_label])

@st.cache_data(show_spinner=False)
def load_data(file_path):
    return pd.read_excel(file_path)

df = load_data(selected_path)

# --- Dropdown State Logic ---
def safe_selectbox(label, options, session_key):
    selected = st.session_state.get(session_key)
    if selected not in options:
        selected = options[0] if options else None
    return st.selectbox(label, options, index=options.index(selected) if selected in options else 0, key=session_key)

# --- Dropdowns ---
models = sorted(df["Model"].dropna().unique())
if not models:
    st.error("❌ No models found")
    st.stop()

col1, col2 = st.columns([2, 1])
with col1:
    model = safe_selectbox("🚘 Select Model", models, "selected_model")

fuel_df = df[df["Model"] == model]
fuel_types = sorted(fuel_df["Fuel Type"].dropna().unique())
if not fuel_types:
    st.error("❌ No fuel types found")
    st.stop()

with col2:
    fuel_type = safe_selectbox("⛽ Select Fuel Type", fuel_types, "selected_fuel")

variant_df = fuel_df[fuel_df["Fuel Type"] == fuel_type]
variants = sorted(variant_df["Variant"].dropna().unique())
if not variants:
    st.error("❌ No variants found")
    st.stop()

variant = safe_selectbox("🎯 Select Variant", variants, "selected_variant")
row = variant_df[variant_df["Variant"] == variant].iloc[0]

# --- Formatter ---
def format_indian_currency(value):
    try:
        if pd.isnull(value): return "<i style='color:gray;'>N/A</i>"
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
    except:
        return "<i style='color:red;'>Invalid</i>"

# --- Table Renderer ---
def render_combined_table(row, shared_fields, grouped_fields, group_keys):
    html = '''
    <div class="table-wrapper">
    <table class="styled-table">
        <tr><th>Description</th><th>Individual</th><th>Corporate</th></tr>
    '''
    for field in shared_fields:
        val = format_indian_currency(row.get(field))
        html += f"<tr><td>{field}</td><td>{val}</td><td>{val}</td></tr>"
    for field in grouped_fields:
        ind_key, corp_key = group_keys.get(field, ("", ""))
        ind_val = format_indian_currency(row.get(ind_key))
        corp_val = format_indian_currency(row.get(corp_key))
        highlight = " style='background-color:#fff3cd;font-weight:bold;'" if field.startswith("On Road") else ""
        html += f"<tr{highlight}><td>{field}</td><td>{ind_val}</td><td>{corp_val}</td></tr>"
    html += "</table></div>"
    return html

# --- Render Output ---
st.title("🚗 Mahindra Vehicle Pricing Viewer")
st.markdown(f"### 🚙 {model} - {fuel_type} - {variant}")
st.subheader("📋 Vehicle Pricing Details")

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

st.markdown(render_combined_table(row, shared_fields, grouped_fields, group_keys), unsafe_allow_html=True)
