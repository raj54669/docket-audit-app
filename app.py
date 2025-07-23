import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime, timedelta
from github import Github

# --- GitHub Repo Setup ---
REPO = "raj54669/docket-audit-app"
DATA_DIR = "Data/Price_List"
g = Github(st.secrets["github_token"])
repo = g.get_repo(REPO)

# --- Page Config ---
st.set_page_config(page_title="Mahindra Pricing Viewer", layout="centered")

# --- Global Styling ---
st.markdown("""<style>
:root {
    --title-size: 40px; --subtitle-size: 18px; --caption-size: 16px;
    --label-size: 14px; --select-font-size: 15px; --table-font-size: 14px;
    --variant-title-size: 20px;
}
.block-container { padding-top: 0rem; }
header {visibility: hidden;}
h1 { font-size: var(--title-size) !important; }
h2 { font-size: var(--subtitle-size) !important; }
h3 { font-size: var(--variant-title-size) !important; }
.stCaption { font-size: var(--caption-size) !important; }
.stSelectbox label {
    font-size: var(--label-size) !important; font-weight: 600 !important;
}
.stSelectbox div[data-baseweb="select"] > div {
    font-size: var(--select-font-size) !important; font-weight: bold !important;
    padding-top: 2px !important; padding-bottom: 2px !important;
    line-height: 1 !important; min-height: 24px !important;
}
.stSelectbox div[data-baseweb="select"] {
    align-items: center !important; height: 28px !important;
}
.stSelectbox [data-baseweb="menu"] > div {
    padding-top: 2px !important; padding-bottom: 2px !important;
}
.stSelectbox [data-baseweb="option"] {
    padding: 4px 10px !important; font-size: var(--select-font-size) !important;
    font-weight: 500 !important; line-height: 1.2 !important;
    min-height: 28px !important;
}
.stSelectbox [data-baseweb="option"]:hover {
    background-color: #f0f0f0 !important; font-weight: 600 !important;
}
.styled-table { font-size: var(--table-font-size) !important; }
</style>""", unsafe_allow_html=True)

# --- Utility Functions ---
@st.cache_data(show_spinner=False)
def load_excel_from_repo(path):
    file = repo.get_contents(path)
    df = pd.read_excel(file.decoded_content)
    return df

@st.cache_data(show_spinner=False)
def get_latest_files():
    files = repo.get_contents(DATA_DIR)
    pattern = r"PV Price List Master D\. (\d{2})\.(\d{2})\.(\d{4})\.xlsx"
    valid_files = []
    for file in files:
        match = re.search(pattern, file.name)
        if match:
            day, month, year = match.groups()
            dt = datetime.strptime(f"{day}-{month}-{year}", "%d-%m-%Y")
            valid_files.append((dt, file.name))
    valid_files.sort(reverse=True)
    return [name for _, name in valid_files[:5]]

def format_indian_currency(value):
    if pd.isnull(value): return "<i style='color:gray;'>N/A</i>"
    try:
        value = float(value)
        s = f"{int(abs(value))}"
        last_three = s[-3:]
        other = re.sub(r'(\d)(?=(\d{2})+$)', r'\1,', s[:-3])
        formatted = f"{other},{last_three}" if other else last_three
        return f"<b>{'-' if value < 0 else ''}₹{formatted}</b>"
    except: return "<i style='color:red;'>Invalid</i>"

def render_combined_table(row, shared_fields, grouped_fields, group_keys):
    html = "<div class='table-wrapper'><table class='styled-table'>"
    html += "<tr><th>Description</th><th>Individual</th><th>Corporate</th></tr>"
    for field in shared_fields:
        val = format_indian_currency(row.get(field))
        html += f"<tr><td>{field}</td><td>{val}</td><td>{val}</td></tr>"
    for field in grouped_fields:
        ind, corp = group_keys[field]
        iv, cv = format_indian_currency(row.get(ind)), format_indian_currency(row.get(corp))
        highlight = " style='background-color:#fff3cd;font-weight:bold;'" if field.startswith("On Road Price") else ""
        html += f"<tr{highlight}><td>{field}</td><td>{iv}</td><td>{cv}</td></tr>"
    html += "</table></div>"
    return html

# --- Table Styling ---
st.markdown("""<style>
.table-wrapper { margin-bottom: 15px; padding: 0; }
.styled-table {
    width: 100%; border-collapse: collapse; table-layout: fixed;
    font-size: 14px; line-height: 1; border: 2px solid black;
}
.styled-table th, .styled-table td {
    border: 1px solid black; padding: 4px 10px; text-align: center; line-height: 1;
}
.styled-table th:nth-child(1), .styled-table td:nth-child(1) { width: 60%; }
.styled-table th:nth-child(2), .styled-table td:nth-child(2),
.styled-table th:nth-child(3), .styled-table td:nth-child(3) { width: 20%; }
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
</style>""", unsafe_allow_html=True)

# --- UI: Title & File Select ---
st.title("🚗 Mahindra Vehicle Pricing Viewer")
all_files = get_latest_files()
if not all_files:
    st.error("❌ No price list files found.")
    st.stop()

selected_file = st.selectbox("📂 Select Price List File", all_files, index=0)
data = load_excel_from_repo(f"{DATA_DIR}/{selected_file}")

# Timestamp
try:
    file = repo.get_contents(f"{DATA_DIR}/{selected_file}")
    updated = datetime.strptime(file.last_modified, "%a, %d %b %Y %H:%M:%S %Z") + timedelta(hours=5, minutes=30)
    st.caption(f"📅 Data last updated on: {updated.strftime('%d-%b-%Y %I:%M %p')} (IST)")
except:
    st.caption("📅 Timestamp not available.")

# --- Dropdowns ---
models = sorted(data["Model"].dropna().unique())
model = st.selectbox("🚘 Select Model", models, key="model")

fuels = sorted(data[data["Model"] == model]["Fuel Type"].dropna().unique())
fuel_type = st.selectbox("⛽ Select Fuel Type", fuels, key="fuel")

variants = sorted(data[(data["Model"] == model) & (data["Fuel Type"] == fuel_type)]["Variant"].dropna().unique())
variant = st.selectbox("🎯 Select Variant", variants, key="variant")

selected_row = data[
    (data["Model"] == model) &
    (data["Fuel Type"] == fuel_type) &
    (data["Variant"] == variant)
]

if selected_row.empty:
    st.warning("⚠️ No data found for selected variant.")
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

# --- Output Table ---
st.markdown(f"### 🚙 {model} - {fuel_type} - {variant}")
st.subheader("📋 Vehicle Pricing Details")
st.markdown(render_combined_table(row, shared_fields, grouped_fields, group_keys), unsafe_allow_html=True)
