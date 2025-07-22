import streamlit as st
import pandas as pd
import os
import re
import base64
import requests
from datetime import datetime

# --- Streamlit Page Setup ---
st.set_page_config(page_title="🚛 Mahindra Docket Audit Tool - CV", layout="centered")

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
        --variant-title-size: 24px;
    }

    .block-container { padding-top: 0rem; }
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

    .stSelectbox [data-baseweb="option"]:hover {
        background-color: #f0f0f0 !important;
        font-weight: 600 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Constants ---
DATA_DIR = "Data/Discount_Cheker"
FILE_PATTERN = r"CV Discount Check Master File (\d{2})\.(\d{2})\.(\d{4})\.xlsx"

# --- GitHub Upload + Auto-Cleanup ---
def upload_to_github(file_path, filename):
    try:
        token = st.secrets["github"]["token"]
        username = st.secrets["github"]["username"]
        repo = st.secrets["github"]["repo"]
        branch = st.secrets["github"].get("branch", "main")
        github_dir = "Data/Discount_Cheker"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }

        github_file_path = f"{github_dir}/{filename}"
        with open(file_path, "rb") as f:
            content = base64.b64encode(f.read()).decode()

        # Check if file exists
        url = f"https://api.github.com/repos/{username}/{repo}/contents/{github_file_path}"
        check = requests.get(url, headers=headers)
        sha = check.json().get("sha") if check.status_code == 200 else None

        payload = {
            "message": f"Upload Excel file {filename}",
            "content": content,
            "branch": branch
        }
        if sha:
            payload["sha"] = sha

        put = requests.put(url, headers=headers, json=payload)
        if put.status_code not in [200, 201]:
            st.sidebar.error(f"❌ GitHub upload failed: {put.json().get('message')}")
            return

        st.sidebar.success(f"✅ Uploaded to GitHub: {filename}")

        # --- Keep only last 5 ---
        list_url = f"https://api.github.com/repos/{username}/{repo}/contents/{github_dir}"
        files_resp = requests.get(list_url, headers=headers)
        if files_resp.status_code != 200:
            st.sidebar.warning("⚠️ Could not fetch file list from GitHub.")
            return

        files_data = files_resp.json()
        excel_files = []
        for item in files_data:
            fname = item["name"]
            match = re.match(FILE_PATTERN, fname)
            if match:
                try:
                    day, month, year = match.groups()
                    fdate = datetime.strptime(f"{day}.{month}.{year}", "%d.%m.%Y")
                    excel_files.append((fname, fdate, item["sha"]))
                except:
                    continue

        excel_files.sort(key=lambda x: x[1], reverse=True)
        for fname, _, sha_to_delete in excel_files[5:]:
            del_url = f"https://api.github.com/repos/{username}/{repo}/contents/{github_dir}/{fname}"
            del_payload = {
                "message": f"Auto-delete old Excel file: {fname}",
                "sha": sha_to_delete,
                "branch": branch
            }
            requests.delete(del_url, headers=headers, json=del_payload)

    except Exception as e:
        st.sidebar.error(f"❌ GitHub Error: {str(e)}")

# --- Sidebar Upload ---
st.sidebar.header("📂 File Selection")

uploaded_file = st.sidebar.file_uploader("Upload New Excel File", type=["xlsx"])
if uploaded_file:
    os.makedirs(DATA_DIR, exist_ok=True)
    save_path = os.path.join(DATA_DIR, uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    upload_to_github(save_path, uploaded_file.name)
    st.rerun()

# --- File Selection ---
def extract_date_from_filename(filename):
    match = re.search(FILE_PATTERN, filename)
    if match:
        try:
            day, month, year = match.groups()
            return datetime.strptime(f"{day}.{month}.{year}", "%d.%m.%Y")
        except:
            return None
    return None

files = []
for fname in os.listdir(DATA_DIR):
    if re.match(FILE_PATTERN, fname):
        dt = extract_date_from_filename(fname)
        if dt:
            files.append((fname, dt))

files = sorted(files, key=lambda x: x[1], reverse=True)[:5]
if not files:
    st.error("❌ No valid Excel files found.")
    st.stop()

file_labels = [f"{fname} ({dt.strftime('%d-%b-%Y')})" for fname, dt in files]
file_map = {label: fname for label, (fname, _) in zip(file_labels, files)}
selected_file_label = st.sidebar.selectbox("📅 Select Excel File", file_labels)
selected_filepath = os.path.join(DATA_DIR, file_map[selected_file_label])

# --- Load Excel ---
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

# --- PAGE TITLE ---
st.title("🚛 Mahindra Docket Audit Tool - CV")

# --- Variant Selection ---
variant_col = "Variant"
if variant_col not in data.columns:
    st.error("❌ 'Variant' column not found.")
    st.stop()

variants = data[variant_col].dropna().drop_duplicates().tolist()
selected_variant = st.selectbox("🎯 Select Vehicle Variant", variants)

filtered = data[data[variant_col] == selected_variant]
if filtered.empty:
    st.warning("⚠️ No data found for selected variant.")
    st.stop()

row = filtered.iloc[0]

# --- VEHICLE PRICING TABLE ---
st.markdown("<h3>📝 Vehicle Pricing Details</h3>", unsafe_allow_html=True)
vehicle_columns = [
    'Ex-Showroom Price', 'TCS', 'Comprehensive + Zero\nDep. Insurance',
    'R.T.O. Charges With\nHypo.', 'RSA (Road Side\nAssistance) For 1\nYear',
    'SMC Road - Tax (If\nApplicable)', 'MAXI CARE', 'Accessories',
    'ON ROAD PRICE\nWith SMC Road Tax', 'ON ROAD PRICE\nWithout SMC Road\nTax',
]
pricing_html = """
<style>
.vtable { border-collapse: collapse; width: 100%; font-weight: bold; font-size: 14px; }
.vtable th { background-color: #004080; color: white !important; padding: 4px 6px; text-align: right; }
.vtable td { background-color: #f0f4f8; padding: 4px 6px; font-weight: bold; text-align: right; color: black !important; }
.vtable td:first-child, .vtable th:first-child { text-align: left; }
.vtable, .vtable th, .vtable td { border: 1px solid #000; }
</style>
<table class='vtable'><tr><th>Description</th><th>Amount</th></tr>
"""
for col in vehicle_columns:
    if col in row:
        pricing_html += f"<tr><td>{col}</td><td>{format_indian_currency(row[col])}</td></tr>"
pricing_html += "</table>"
st.markdown(pricing_html, unsafe_allow_html=True)

# --- CARTEL OFFER TABLE ---
st.markdown("<h3>🎁 Cartel Offer</h3>", unsafe_allow_html=True)
cartel_columns = [
    'M&M\nScheme with\nGST',
    'Dealer Offer ( Without Exchange Case)',
    'Dealer Offer ( If Exchange Case)'
]
cartel_html = """
<style>
.ctable { border-collapse: collapse; width: 100%; font-weight: bold; font-size: 14px; }
.ctable th { background-color: #2e7d32; color: white !important; padding: 4px 6px; text-align: right; }
.ctable td { background-color: #e8f5e9; padding: 4px 6px; font-weight: bold; text-align: right; color: black !important; }
.ctable td:first-child, .ctable th:first-child { text-align: left; }
.ctable, .ctable th, .ctable td { border: 1px solid #000; }
</style>
<table class='ctable'><tr><th>Description</th><th>Offer</th></tr>
"""
for col in cartel_columns:
    if col in row:
        val = format_indian_currency(row[col]) if "GST" in col else row[col]
        cartel_html += f"<tr><td>{col}</td><td>{val}</td></tr>"
cartel_html += "</table>"
st.markdown(cartel_html, unsafe_allow_html=True)
