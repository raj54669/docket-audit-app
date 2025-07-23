# --- Imports ---
import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime, timedelta
import base64
import requests

# --- Configuration ---
st.set_page_config(page_title="Mahindra Vehicle Pricing Viewer", layout="centered")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
REPO = st.secrets["REPO"]
DATA_DIR = st.secrets["DATA_DIR"]
GITHUB_API = "https://api.github.com"

# --- Styling ---
st.markdown("""<style>
    header {visibility: hidden;}
    .block-container { padding-top: 0rem; }
</style>""", unsafe_allow_html=True)

# --- Helper Functions ---
def extract_date_from_filename(name):
    match = re.search(r'(\d{2}\.\d{2}\.\d{4})', name)
    if match:
        return datetime.strptime(match.group(1), "%d.%m.%Y")
    return datetime.min

@st.cache_data(show_spinner=False)
def list_files():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    url = f"{GITHUB_API}/repos/{REPO}/contents/{DATA_DIR}"
    resp = requests.get(url, headers=headers)
    files = resp.json()
    valid_files = []
    for f in files:
        if f["name"].endswith(".xlsx"):
            date = extract_date_from_filename(f["name"])
            valid_files.append({"name": f["name"], "date": date})
    sorted_files = sorted(valid_files, key=lambda x: x["date"], reverse=True)
    return sorted_files[:5]

def get_download_url(filename):
    return f"https://raw.githubusercontent.com/{REPO}/main/{DATA_DIR}/{filename}"

def upload_to_github(uploaded_file):
    content = base64.b64encode(uploaded_file.read()).decode("utf-8")
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    path = f"{DATA_DIR}/{uploaded_file.name}"
    url = f"{GITHUB_API}/repos/{REPO}/contents/{path}"

    # Check if file exists
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        sha = res.json()["sha"]
        data = {
            "message": f"Update {uploaded_file.name}",
            "content": content,
            "sha": sha,
        }
    else:
        data = {
            "message": f"Add {uploaded_file.name}",
            "content": content,
        }

    resp = requests.put(url, headers=headers, json=data)
    return resp.ok

def load_data(file_url):
    return pd.read_excel(file_url)

def format_indian_currency(value):
    if pd.isnull(value): return "<i style='color:gray;'>N/A</i>"
    try:
        value = float(value)
        is_neg = value < 0
        value = abs(value)
        s = f"{int(value)}"
        last3 = s[-3:]
        other = s[:-3]
        if other: other = re.sub(r'(\d)(?=(\d{2})+$)', r'\1,', other)
        formatted = f"{other},{last3}" if other else last3
        result = f"₹{formatted}"
        return f"<b>{'-' if is_neg else ''}{result}</b>"
    except:
        return "<i style='color:red;'>Invalid</i>"

def render_combined_table(row, shared_fields, grouped_fields, group_keys):
    html = """<div class="table-wrapper"><table class="styled-table">
        <tr><th>Description</th><th>Individual</th><th>Corporate</th></tr>"""
    for field in shared_fields:
        val = format_indian_currency(row.get(field))
        html += f"<tr><td>{field}</td><td>{val}</td><td>{val}</td></tr>"
    for field in grouped_fields:
        ind_key, corp_key = group_keys.get(field, ("", ""))
        ind_val = format_indian_currency(row.get(ind_key))
        corp_val = format_indian_currency(row.get(corp_key))
        highlight = " style='background-color:#fff3cd;font-weight:bold;'" if field.startswith("On Road Price") else ""
        html += f"<tr{highlight}><td>{field}</td><td>{ind_val}</td><td>{corp_val}</td></tr>"
    html += "</table></div>"
    return html

# --- Sidebar: Admin Login & Upload ---
with st.sidebar.expander("🔐 Admin Login", expanded=True):
    pwd = st.text_input("Enter admin password:", type="password")
    if st.button("Login"):
        if pwd == ADMIN_PASSWORD:
            st.session_state.admin = True
            st.success("Logged in ✅")
        else:
            st.error("Incorrect password ❌")

if st.session_state.get("admin"):
    uploaded = st.sidebar.file_uploader("📤 Upload new pricing file", type="xlsx")
    if uploaded and st.sidebar.button("Upload"):
        if upload_to_github(uploaded):
            st.sidebar.success("✅ File uploaded.")
            st.cache_data.clear()
        else:
            st.sidebar.error("❌ Upload failed.")

# --- Main Page Title ---
st.title("🚗 Mahindra Vehicle Pricing Viewer")

# --- File Selection Dropdown ---
file_list = list_files()
file_names = [f"{f['name']} ({f['date'].strftime('%d-%b-%Y')})" for f in file_list]
file_lookup = {f"{f['name']} ({f['date'].strftime('%d-%b-%Y')})": f["name"] for f in file_list}
default_file = file_names[0] if file_names else None

sel_file = st.selectbox("📂 Select File", file_names, index=0, key="selected_file")
file_url = get_download_url(file_lookup[sel_file])
df = load_data(file_url)

# --- Extract Dropdown Values ---
models = sorted(df["Model"].dropna().unique())
sel_model = st.selectbox("Model", models, key="sel_model")

fuel_df = df[df["Model"] == sel_model]
fuel_types = sorted(fuel_df["Fuel Type"].dropna().unique())
if fuel_types:
    if st.session_state.get("sel_fuel_type") not in fuel_types:
        st.session_state["sel_fuel_type"] = fuel_types[0]
    sel_fuel = st.selectbox("Fuel Type", fuel_types, key="sel_fuel_type")
else:
    st.error("❌ No fuel types for this model."); st.stop()

variant_df = fuel_df[fuel_df["Fuel Type"] == sel_fuel]
variants = sorted(variant_df["Variant"].dropna().unique())
if variants:
    if st.session_state.get("sel_variant") not in variants:
        st.session_state["sel_variant"] = variants[0]
    sel_variant = st.selectbox("Variant", variants, key="sel_variant")
else:
    st.error("❌ No variants for this fuel type."); st.stop()

selected_row = variant_df[variant_df["Variant"] == sel_variant]
if selected_row.empty:
    st.warning("⚠️ No data found."); st.stop()
row = selected_row.iloc[0]

# --- Display Table ---
st.markdown(f"### 🚙 {sel_model} - {sel_fuel} - {sel_variant}")
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
