import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime

st.set_page_config(page_title="🚛 Mahindra Docket Audit Tool - CV", layout="centered")

# ✨ Global Styling (Dropdown style updated)
st.markdown("""
    <style>
    :root {
        --title-size: 40px;
        --subtitle-size: 18px;
        --caption-size: 16px;
        --label-size: 14px;
        --select-font-size: 15px;
        --table-font-size: 14px;
        --variant-title-size: 24px;
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
    </style>
""", unsafe_allow_html=True)

# --- Constants ---
DATA_DIR = "Data/Discount_Cheker"
FILE_PATTERN = r"CV Discount Check Master File (\d{2})\.(\d{2})\.(\d{4})\.xlsx"

# --- Sidebar: Upload File ---
st.sidebar.header("📂 File Selection")

uploaded_file = st.sidebar.file_uploader("Upload New Excel File", type=["xlsx"])
if uploaded_file:
    save_path = os.path.join(DATA_DIR, uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success(f"✅ Uploaded: {uploaded_file.name}")
    st.rerun()


# --- File Scanner ---
def extract_date_from_filename(filename):
    match = re.search(FILE_PATTERN, filename)
    if match:
        day, month, year = match.groups()
        try:
            return datetime.strptime(f"{day}.{month}.{year}", "%d.%m.%Y")
        except:
            return None
    return None

files = []
for fname in os.listdir(DATA_DIR):
    if re.match(FILE_PATTERN, fname):
        date_obj = extract_date_from_filename(fname)
        if date_obj:
            files.append((fname, date_obj))

# Sort and keep last 5
files = sorted(files, key=lambda x: x[1], reverse=True)[:5]
if not files:
    st.error("❌ No valid Excel files found.")
    st.stop()

file_labels = [f"{fname} ({dt.strftime('%d-%b-%Y')})" for fname, dt in files]
file_map = {label: fname for label, (fname, _) in zip(file_labels, files)}

selected_file_label = st.sidebar.selectbox("📅 Select Excel File", file_labels)
selected_filename = file_map[selected_file_label]
selected_filepath = os.path.join(DATA_DIR, selected_filename)

# --- Load Data ---
@st.cache_data(show_spinner=False)
def load_data(path):
    return pd.read_excel(path, header=1)

data = load_data(selected_filepath)

# --- Currency Formatter ---
def format_indian_currency(value):
    try:
        if pd.isnull(value) or value == 0:
            return "₹0"
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
        return f"-{result}" if is_negative else result
    except:
        return "Invalid"

# --- Variant Filter ---
variant_col = "Variant"
if variant_col not in data.columns:
    st.error("❌ 'Variant' column not found in selected file.")
    st.stop()

variants = data[variant_col].dropna().drop_duplicates().tolist()
selected_variant = st.sidebar.selectbox("🚙 Select Vehicle Variant", variants)

filtered = data[data[variant_col] == selected_variant]
if filtered.empty:
    st.warning("⚠️ No data found for selected variant.")
    st.stop()

row = filtered.iloc[0]

# --- PAGE TITLE ---
st.title("🚛 Mahindra Docket Audit Tool - CV")

# --- VEHICLE PRICING TABLE ---
vehicle_columns = [
    'Ex-Showroom Price', 'TCS', 'Comprehensive + Zero\nDep. Insurance',
    'R.T.O. Charges With\nHypo.', 'RSA (Road Side\nAssistance) For 1\nYear',
    'SMC Road - Tax (If\nApplicable)', 'MAXI CARE', 'Accessories',
    'ON ROAD PRICE\nWith SMC Road Tax', 'ON ROAD PRICE\nWithout SMC Road\nTax',
]

st.markdown("<h3>📝 Vehicle Pricing Details</h3>", unsafe_allow_html=True)
pricing_html = """
<style>
.vtable {
    border-collapse: collapse;
    width: 100%;
    font-weight: bold;
    font-size: 14px;
}
.vtable th {
    background-color: #004080;
    color: white !important;
    padding: 4px 6px;
    text-align: right;
}
.vtable td {
    background-color: #f0f4f8;
    padding: 4px 6px;
    font-weight: bold;
    text-align: right;
    color: black !important;
}
.vtable td:first-child, .vtable th:first-child {
    text-align: left;
}
.vtable, .vtable th, .vtable td {
    border: 1px solid #000;
}
</style>
<table class='vtable'>
<tr><th>Description</th><th>Amount</th></tr>
"""
for col in vehicle_columns:
    if col in row:
        val = row[col]
        val_fmt = format_indian_currency(val)
        pricing_html += f"<tr><td>{col}</td><td>{val_fmt}</td></tr>"
pricing_html += "</table>"
st.markdown(pricing_html, unsafe_allow_html=True)

# --- CARTEL OFFER TABLE ---
cartel_columns = [
    'M&M\nScheme with\nGST',
    'Dealer Offer ( Without Exchange Case)',
    'Dealer Offer ( If Exchange Case)'
]

st.markdown("<h3>🎁 Cartel Offer</h3>", unsafe_allow_html=True)
cartel_html = """
<style>
.ctable {
    border-collapse: collapse;
    width: 100%;
    font-weight: bold;
    font-size: 14px;
}
.ctable th {
    background-color: #2e7d32;
    color: white !important;
    padding: 4px 6px;
    text-align: right;
}
.ctable td {
    background-color: #e8f5e9;
    padding: 4px 6px;
    font-weight: bold;
    text-align: right;
    color: black !important;
}
.ctable td:first-child, .ctable th:first-child {
    text-align: left;
}
.ctable, .ctable th, .ctable td {
    border: 1px solid #000;
}
</style>
<table class='ctable'>
<tr><th>Description</th><th>Offer</th></tr>
"""
for col in cartel_columns:
    if col in row:
        val = row[col]
        if col.strip() == "M&M\nScheme with\nGST":
            val = format_indian_currency(val)
        cartel_html += f"<tr><td>{col}</td><td>{val}</td></tr>"
cartel_html += "</table>"
st.markdown(cartel_html, unsafe_allow_html=True)
