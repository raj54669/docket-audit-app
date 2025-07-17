import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os, re

# --- Config & Constants ---
st.set_page_config(page_title="Mahindra Pricing Viewer", layout="centered")  # Changed from "wide"
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
    field: (f"{field} - Individual", f"{field} - Corporate")
    for field in GROUPED_FIELDS
}

# --- Styles ---
st.markdown("""
<style>
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
    max-width: 900px;
    margin: auto;
}
.table-wrapper {
    margin-bottom: 15px;
    padding: 0;
    overflow-x: auto;
    max-width: 100%;
}
.styled-table {
    width: 100%;
    max-width: 800px;
    margin: auto;
    border-collapse: collapse;
    font-size: 16px;
    line-height: 1.2;
    border: 2px solid black;
}
.styled-table th, .styled-table td {
    border: 1px solid black;
    padding: 8px 10px;
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
</style>
""", unsafe_allow_html=True)

# --- Helpers ---
@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        st.error("❌ Pricing file not found."); st.stop()
    try:
        return pd.read_excel(path)
    except Exception as e:
        st.error(f"❌ Failed to load Excel file: {e}"); st.stop()

def format_indian_currency(value) -> str:
    if pd.isnull(value): return "<i style='color:gray;'>N/A</i>"
    try:
        val = abs(float(value)); neg = "-" if float(value) < 0 else ""
        s = str(int(val)); last3, rest = s[-3:], s[:-3]
        if rest: rest = re.sub(r'(\d)(?=(\d{2})+$)', r'\1,', rest)
        return f"<b>{neg}₹{rest + ',' if rest else ''}{last3}</b>"
    except: return "<i style='color:red;'>Invalid</i>"

def render_table(row: pd.Series, fields: list, header: list) -> str:
    rows = "".join(f"<tr>{''.join(f'<td>{cell}</td>' for cell in line)}</tr>" for line in fields)
    return f"<div class='table-wrapper'><table class='styled-table'><tr>{''.join(f'<th>{h}</th>' for h in header)}</tr>{rows}</table></div>"

def render_shared_table(row, fields): return render_table(
    row, [(f, format_indian_currency(row.get(f))) for f in fields], ["Description", "Amount"]
)

def render_registration_table(row, groups, keys): return render_table(
    row, [(g, format_indian_currency(row.get(keys[g][0])), format_indian_currency(row.get(keys[g][1]))) for g in groups],
    ["Registration", "Individual", "Corporate"]
)

# --- App Logic ---
st.title("🚗 Mahindra Vehicle Pricing Viewer")

df = load_data(FILE_PATH)

try:
    ts = datetime.fromtimestamp(os.path.getmtime(FILE_PATH)) + timedelta(hours=5, minutes=30)
    st.caption(f"📅 Data last updated on: {ts.strftime('%d-%b-%Y %I:%M %p')} (IST)")
except: st.caption("📅 Last update timestamp not available.")

models = sorted(df["Model"].dropna().unique())
if not models: st.error("❌ No models found in data."); st.stop()

col1, col2 = st.columns(2)
with col1: model = st.selectbox("🚘 Select Model", models)

fuel_df = df[df["Model"] == model]
fuel_types = sorted(fuel_df["Fuel Type"].dropna().unique())
if not fuel_types: st.error("❌ No fuel types found for selected model."); st.stop()

with col2: fuel_type = st.selectbox("⛽ Select Fuel Type", fuel_types)

variant_df = fuel_df[fuel_df["Fuel Type"] == fuel_type]
variants = sorted(variant_df["Variant"].dropna().unique())
if not variants: st.error("❌ No variants available."); st.stop()

variant = st.selectbox("🎯 Select Variant", variants)
row_df = variant_df[variant_df["Variant"] == variant]
if row_df.empty: st.warning("⚠️ No data found for selected filters."); st.stop()

row = row_df.iloc[0]
st.subheader("📋 Vehicle Pricing Details")
st.markdown(render_shared_table(row, SHARED_FIELDS), unsafe_allow_html=True)
st.markdown(render_registration_table(row, GROUPED_FIELDS, GROUP_KEYS), unsafe_allow_html=True)
