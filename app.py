# streamlit_app.py (Final Full Version with Admin Upload + Title Fix + Dropdowns + Table)
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

# --- Admin Auth ---
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

def upload_to_github(file_path, filename):
    token = st.secrets["github"]["token"]
    username = st.secrets["github"]["username"]
    repo = st.secrets["github"]["repo"]
    branch = st.secrets["github"].get("branch", "main")
    github_dir = "Data/Price_List"

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
        return

    files_data = files_resp.json()
    excel_files = []
    for item in files_data:
        fname = item["name"]
        match = re.match(FILE_PATTERN, fname)
        if match:
            try:
                dt = datetime.strptime(".".join(match.groups()), "%d.%m.%Y")
                excel_files.append((fname, dt, item["sha"]))
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

# --- Title First ---
st.title("🚗 Mahindra Vehicle Pricing Viewer")

# --- Upload (if admin) ---
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

# --- Get List of Excel Files ---
def extract_date_from_filename(fname):
    m = re.match(FILE_PATTERN, fname)
    if m:
        try:
            return datetime.strptime(".".join(m.groups()), "%d.%m.%Y")
        except:
            return None

os.makedirs(DATA_DIR, exist_ok=True)
files = [f for f in os.listdir(DATA_DIR) if re.match(FILE_PATTERN, f)]
files_with_dates = [(f, extract_date_from_filename(f)) for f in files]
files_with_dates = sorted([f for f in files_with_dates if f[1]], key=lambda x: x[1], reverse=True)[:5]
if not files_with_dates:
    st.error("❌ No valid Excel files found.")
    st.stop()

file_labels = [f"{fname} ({dt.strftime('%d-%b-%Y')})" for fname, dt in files_with_dates]
file_map = {label: fname for label, (fname, _) in zip(file_labels, files_with_dates)}

selected_file_label = st.selectbox("📅 Select Excel File", file_labels, key="file_select")
selected_file = os.path.join(DATA_DIR, file_map[selected_file_label])
data = pd.read_excel(selected_file)

# --- Dropdowns ---
models = sorted(data["Model"].dropna().unique())
col1, col2 = st.columns([2, 1])
with col1:
    model = st.selectbox("🚘 Select Model", models, key="model_select")
fuel_df = data[data["Model"] == model]
fuels = sorted(fuel_df["Fuel Type"].dropna().unique())
with col2:
    fuel_type = st.selectbox("⛽ Select Fuel Type", fuels, key="fuel_select")

variant_df = fuel_df[fuel_df["Fuel Type"] == fuel_type]
variants = sorted(variant_df["Variant"].dropna().unique())
variant = st.selectbox("🎯 Select Variant", variants, key="variant_select")
selected_row = variant_df[variant_df["Variant"] == variant]
if selected_row.empty:
    st.warning("⚠️ No data found for selected filters.")
    st.stop()
row = selected_row.iloc[0]

# --- Currency Format ---
def format_indian_currency(value):
    try:
        if pd.isnull(value): return "<i>N/A</i>"
        value = float(value)
        is_neg = value < 0
        value = abs(value)
        s = f"{int(value)}"
        last = s[-3:]; other = s[:-3]
        if other:
            other = re.sub(r'(\d)(?=(\d{2})+$)', r'\1,', other)
            formatted = f"{other},{last}"
        else:
            formatted = last
        result = f"₹{formatted}"
        return f"<b>{'-' if is_neg else ''}{result}</b>"
    except:
        return "<i>Invalid</i>"

# --- Combined Table ---
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
    "On Road Price (With HYPO)": ("On Road Price (With HYPO) - Individual", "On Road Price (With HYPO) - Corporate")
}

st.markdown(f"### 🚙 {model} - {fuel_type} - {variant}")
st.subheader("📋 Vehicle Pricing Details")

html = '''
<div class="table-wrapper">
<table class="styled-table">
<tr><th>Description</th><th>Individual</th><th>Corporate</th></tr>
'''
for field in shared_fields:
    val = format_indian_currency(row.get(field))
    html += f"<tr><td>{field}</td><td>{val}</td><td>{val}</td></tr>"
for field in grouped_fields:
    ind_key, corp_key = group_keys[field]
    ind_val = format_indian_currency(row.get(ind_key))
    corp_val = format_indian_currency(row.get(corp_key))
    highlight = " style='background-color:#fff3cd;font-weight:bold;'" if "On Road" in field else ""
    html += f"<tr{highlight}><td>{field}</td><td>{ind_val}</td><td>{corp_val}</td></tr>"
html += "</table></div>"
st.markdown(html, unsafe_allow_html=True)

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
    width: 60%; text-align: left; font-weight: 600; background-color: #004d40; color: white;
}
.styled-table th:nth-child(2), .styled-table td:nth-child(2),
.styled-table th:nth-child(3), .styled-table td:nth-child(3) {
    width: 20%; background-color: #fff; color: black;
}
@media (prefers-color-scheme: dark) {
    .styled-table th, .styled-table td { border-color: white; }
    .styled-table td { background-color: #111; color: #eee; }
    .styled-table td:first-child { background-color: #1e1e1e; color: white; }
}
</style>
""", unsafe_allow_html=True)
