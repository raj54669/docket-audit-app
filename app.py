import streamlit as st
import pandas as pd
import os
import re
import base64
import requests
from datetime import datetime, timedelta

# --- Page Config ---
st.set_page_config(page_title="Mahindra Vehicle Pricing Viewer", layout="centered")

# --- Constants ---
REPO = "raj54669/docket-audit-app"
UPLOAD_DIR = "Data/Price_List"
DATA_DIR = "Data/Price_List"
FILE_PATTERN = r"PV Price List Master D\. (\d{2})\.(\d{2})\.(\d{4})\.xlsx"

# --- Styling (optional: paste your existing CSS here) ---

# --- Admin Login & GitHub Upload ---
def check_admin():
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    if not st.session_state.admin_authenticated:
        with st.sidebar.expander("🔐 Admin Login", expanded=True):
            pwd = st.text_input("Enter admin password:", type="password")
            if st.button("Login"):
                if pwd == st.secrets["auth"]["admin_password"]:
                    st.session_state.admin_authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Incorrect password")
    return st.session_state.admin_authenticated

def logout_admin():
    if st.session_state.get("admin_authenticated", False):
        if st.sidebar.button("🔓 Logout Admin"):
            st.session_state.admin_authenticated = False
            st.rerun()

def upload_to_github(file_path, filename):
    try:
        token = st.secrets["github"]["token"]
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }
        url = f"https://api.github.com/repos/{REPO}/contents/{UPLOAD_DIR}/{filename}"

        with open(file_path, "rb") as f:
            content = base64.b64encode(f.read()).decode()

        check = requests.get(url, headers=headers)
        sha = check.json().get("sha") if check.status_code == 200 else None

        payload = {"message": f"Upload file {filename}", "content": content, "branch": "main"}
        if sha:
            payload["sha"] = sha

        put = requests.put(url, headers=headers, json=payload)
        if put.status_code not in [200, 201]:
            st.sidebar.error(f"GitHub upload failed: {put.json().get('message')}")
        else:
            st.sidebar.success(f"✅ Uploaded to GitHub: {filename}")

    except Exception as e:
        st.sidebar.error(f"GitHub Error: {e}")

# --- Admin Upload Section ---
if check_admin():
    st.sidebar.header("📤 Upload Excel File")
    up = st.sidebar.file_uploader("Upload new .xlsx file", type=["xlsx"])
    if up:
        tmp = os.path.join("/tmp", up.name)
        with open(tmp, "wb") as f:
            f.write(up.getbuffer())
        upload_to_github(tmp, up.name)
        st.rerun()
logout_admin()

# --- File Listing ---
def extract_date(name):
    m = re.search(FILE_PATTERN, name)
    if m:
        try:
            return datetime.strptime(".".join(m.groups()), "%d.%m.%Y")
        except:
            return None
    return None

files = [(f, extract_date(f)) for f in os.listdir(DATA_DIR) if re.match(FILE_PATTERN, f)]
files = sorted([fi for fi in files if fi[1]], key=lambda x: x[1], reverse=True)[:5]

if not files:
    st.error("❌ No valid Excel files found.")
    st.stop()

file_labels = [f"{fname} ({dt.strftime('%d-%b-%Y')})" for fname, dt in files]
file_map = {label: fname for label, (fname, _) in zip(file_labels, files)}

st.title("🚗 Mahindra Vehicle Pricing Viewer")
selected_label = st.selectbox("📂 Select File", file_labels, key="selected_excel")
selected_path = os.path.join(DATA_DIR, file_map[selected_label])

# --- Load Excel ---
@st.cache_data
def load_data(path):
    return pd.read_excel(path)

df = load_data(selected_path)
df.columns = [str(c).strip() for c in df.columns]

# --- Dropdowns (Preserve State) ---
def dropdown(col, key):
    opts = sorted(df[col].dropna().unique())
    prev = st.session_state.get(key)
    if prev not in opts:
        prev = opts[0] if opts else None
    sel = st.selectbox(col, opts, index=opts.index(prev) if prev else 0, key=key)
    st.session_state[key] = sel
    return sel

model = dropdown("Model", "sel_model")
fuel_df = df[df["Model"] == model]
fuel = dropdown("Fuel Type", "sel_fuel") if fuel_df.shape[0] else None
var_df = fuel_df[fuel_df["Fuel Type"] == fuel] if fuel else fuel_df
variant = dropdown("Variant", "sel_variant") if var_df.shape[0] else None

row = var_df[var_df["Variant"] == variant].iloc[0] if variant else None

# --- Table Renderer ---
def format_indian_currency(value):
    if pd.isnull(value): return "N/A"
    try:
        value = float(value)
        sign = "-" if value < 0 else ""
        value = abs(int(value))
        s = f"{value:,}".replace(",", "x").replace(".", ",").replace("x", ",")
        if len(s) > 3:
            parts = s.split(",")
            s = ",".join([parts[0]] + [",".join(parts[1:])])
        return f"{sign}₹{s}"
    except:
        return "Invalid"

if row is not None:
    st.subheader(f"📋 Vehicle Pricing: {model} - {fuel} - {variant}")
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

    st.markdown("""
    <style>
    .styled-table {
        width: 100%; border-collapse: collapse;
        font-size: 14px; table-layout: fixed;
    }
    .styled-table th, .styled-table td {
        border: 1px solid black; padding: 4px; text-align: center;
    }
    .styled-table th:first-child, .styled-table td:first-child {
        text-align: left; background-color: #f0f0f0; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

    html = "<table class='styled-table'><tr><th>Description</th><th>Individual</th><th>Corporate</th></tr>"
    for field in shared_fields:
        val = format_indian_currency(row.get(field))
        html += f"<tr><td>{field}</td><td>{val}</td><td>{val}</td></tr>"
    for field in grouped_fields:
        ind_key, corp_key = group_keys[field]
        ind_val = format_indian_currency(row.get(ind_key))
        corp_val = format_indian_currency(row.get(corp_key))
        html += f"<tr><td>{field}</td><td>{ind_val}</td><td>{corp_val}</td></tr>"
    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)
