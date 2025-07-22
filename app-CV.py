import streamlit as st
import pandas as pd
import os
import re
import base64
import requests
from datetime import datetime

# --- Page Config ---
st.set_page_config(page_title="🚛 Mahindra Docket Audit Tool - CV", layout="centered")

# --- Constants ---
DATA_DIR = "Data/Discount_Cheker"
FILE_PATTERN = r"CV Discount Check Master File (\d{2})\.(\d{2})\.(\d{4})\.xlsx"
SHEET_NAME = "Sheet1"
HEADER_ROW = 1

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
.block-container { padding-top: 0.5rem !important; padding-bottom: 0 !important; }
header {visibility: hidden;}
h1 { font-size: var(--title-size) !important; margin-bottom: 0rem !important; }
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

# --- Admin Authentication ---
def check_admin_password():
    correct_password = st.secrets["auth"]["admin_password"]
    if "admin_authenticated" not in st.session_state:
        st.session_state["admin_authenticated"] = False

    if not st.session_state["admin_authenticated"]:
        with st.sidebar.expander("🔐 Admin Login", expanded=True):
            pwd = st.text_input("Enter admin password:", type="password", key="admin_pwd")
            if st.button("Login", key="admin_login_btn"):
                if pwd == correct_password:
                    st.session_state["admin_authenticated"] = True
                    st.rerun()
                else:
                    st.error("❌ Incorrect password.")
        return False
    return True

def logout_admin():
    if st.session_state.get("admin_authenticated", False):
        if st.sidebar.button("🔓 Logout Admin"):
            st.session_state["admin_authenticated"] = False
            st.rerun()

# --- GitHub Upload + Cleanup ---
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

        # Cleanup old files
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

# --- Upload Section (Admin Only) ---
if check_admin_password():
    st.sidebar.header("📂 File Upload (Admin Only)")
    uploaded_file = st.sidebar.file_uploader("Upload New Excel File", type=["xlsx"])
    if uploaded_file:
        os.makedirs(DATA_DIR, exist_ok=True)
        save_path = os.path.join(DATA_DIR, uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        upload_to_github(save_path, uploaded_file.name)
        st.rerun()
logout_admin()

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

files = [(f, extract_date_from_filename(f)) for f in os.listdir(DATA_DIR) if re.match(FILE_PATTERN, f)]
files = sorted([f for f in files if f[1]], key=lambda x: x[1], reverse=True)[:5]
if not files:
    st.error("❌ No valid Excel files found.")
    st.stop()

file_labels = [f"{fname} ({dt.strftime('%d-%b-%Y')})" for fname, dt in files]
file_map = {label: fname for label, (fname, _) in zip(file_labels, files)}

# --- Title ---
st.markdown("<h1>🚛 Mahindra Docket Audit Tool - CV</h1>", unsafe_allow_html=True)

# --- Compact Dropdown Row: Excel + Variant ---
file_col, variant_col = st.columns([1, 1])

with file_col:
    selected_file_label = st.selectbox("📅 Select Excel File", file_labels, key="main_excel_select")
    selected_filepath = os.path.join(DATA_DIR, file_map[selected_file_label])

with variant_col:
    st.markdown("<div id='variant'></div>", unsafe_allow_html=True)
    data = pd.read_excel(selected_filepath, sheet_name=SHEET_NAME, header=HEADER_ROW)
    data.drop(data.columns[0], axis=1, inplace=True)
    data.columns = [str(col).strip().replace("\n", " ").replace("  ", " ") for col in data.columns]

    current_variants = data["Variant"].dropna().drop_duplicates().tolist()

    if "selected_variant" not in st.session_state:
        st.session_state.selected_variant = None

    if st.session_state.selected_variant not in current_variants:
        st.session_state.selected_variant = current_variants[0] if current_variants else None

    selected_variant = st.selectbox(
        "🎯 Select Vehicle Variant",
        current_variants,
        index=current_variants.index(st.session_state.selected_variant),
        key="variant_selectbox"
    )
    st.session_state.selected_variant = selected_variant

# --- Filter by Variant ---
filtered = data[data["Variant"] == selected_variant]
if filtered.empty:
    st.warning("⚠️ No data found for selected variant.")
    st.stop()
row = filtered.iloc[0]

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

# --- Vehicle Pricing Table ---
st.markdown("<h3>📝 Vehicle Pricing Details</h3>", unsafe_allow_html=True)
vehicle_cols = [
    "Ex-Showroom Price", "TCS", "Comprehensive + Zero Dep. Insurance",
    "R.T.O. Charges With Hypo.", "RSA (Road Side Assistance) For 1 Year",
    "SMC Road - Tax (If Applicable)", "MAXI CARE", "Accessories",
    "ON ROAD PRICE With SMC Road Tax", "ON ROAD PRICE Without SMC Road Tax"
]
pricing_html = """
<style>
.vtable { border-collapse: collapse; width: 100%; font-weight: bold; font-size: 14px; }
.vtable th { background-color: #004080; color: white; padding: 4px 6px; text-align: right; }
.vtable td { background-color: #f0f4f8; padding: 4px 6px; text-align: right; color: black; }
.vtable td:first-child, .vtable th:first-child { text-align: left; }
.vtable, .vtable th, .vtable td { border: 1px solid #000; }
</style>
<table class='vtable'><tr><th>Description</th><th>Amount</th></tr>
"""
for col in vehicle_cols:
    pricing_html += f"<tr><td>{col}</td><td>{format_indian_currency(row[col])}</td></tr>"
pricing_html += "</table>"
st.markdown(pricing_html, unsafe_allow_html=True)

# --- Cartel Offer Table ---
st.markdown("<h3>🎁 Cartel Offer</h3>", unsafe_allow_html=True)
cartel_cols = [
    "M&M Scheme with GST",
    "Dealer Offer ( Without Exchange Case)",
    "Dealer Offer ( If Exchange Case)"
]
cartel_html = """
<style>
.ctable { border-collapse: collapse; width: 100%; font-weight: bold; font-size: 14px; }
.ctable th { background-color: #2e7d32; color: white; padding: 4px 6px; text-align: right; }
.ctable td { background-color: #e8f5e9; padding: 4px 6px; text-align: right; color: black; }
.ctable td:first-child, .ctable th:first-child { text-align: left; }
.ctable, .ctable th, .ctable td { border: 1px solid #000; }
</style>
<table class='ctable'><tr><th>Description</th><th>Offer</th></tr>
"""
for col in cartel_cols:
    val = row[col]
    if "scheme" in col.lower():
        val = format_indian_currency(val)
    cartel_html += f"<tr><td>{col}</td><td>{val}</td></tr>"
cartel_html += "</table>"
st.markdown(cartel_html, unsafe_allow_html=True)
