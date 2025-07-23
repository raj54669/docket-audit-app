import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import re
import base64
import requests

# --- Page Configuration ---
st.set_page_config(
    page_title="Mahindra Pricing Viewer",
    layout="centered",
    initial_sidebar_state="auto"
)

# --- Styling (unchanged, omitted for brevity) ---
# You can paste the full style block here from your original code if needed

# --- Authentication ---
def admin_login():
    st.sidebar.header("🔒 Admin Login")
    password = st.sidebar.text_input("Enter Admin Password", type="password")
    if password == st.secrets["auth"]["admin_password"]:
        st.sidebar.success("Access granted.")
        return True
    elif password:
        st.sidebar.error("Invalid password.")
    return False

# --- GitHub Upload ---
def upload_to_github(file):
    token = st.secrets["github"]["token"]
    repo = st.secrets["github"]["REPO"]
    path = st.secrets["github"]["DATA_DIR"] + "/" + file.name
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    content = base64.b64encode(file.read()).decode("utf-8")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    data = {
        "message": f"Upload {file.name}",
        "content": content
    }
    r = requests.put(url, json=data, headers=headers)
    if r.status_code in [200, 201]:
        st.success(f"✅ Uploaded {file.name} to GitHub")
    else:
        st.error(f"❌ GitHub upload failed: {r.json().get('message')}")

# --- Get File List from GitHub ---
@st.cache_data(show_spinner=False)
def get_file_list():
    token = st.secrets["github"]["token"]
    repo = st.secrets["github"]["REPO"]
    path = st.secrets["github"]["DATA_DIR"]
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers)
    files = r.json()
    xls_files = [f['name'] for f in files if f['name'].endswith('.xlsx')]
    xls_files.sort(key=lambda x: datetime.strptime(re.findall(r"\d{2}\.\d{2}\.\d{4}", x)[0], "%d.%m.%Y"), reverse=True)
    return xls_files[:5]  # return latest 5 files

# --- Load Excel Data ---
@st.cache_data(show_spinner=False)
def load_data(file_name):
    path = os.path.join("Data", "Price_List", file_name)
    if not os.path.exists(path):
        st.error("❌ Pricing file not found.")
        st.stop()
    try:
        return pd.read_excel(path)
    except Exception as e:
        st.error(f"❌ Failed to load Excel file: {e}")
        st.stop()

# --- UI Begins ---
st.title("🚗 Mahindra Vehicle Pricing Viewer")

admin_mode = admin_login()

if admin_mode:
    uploaded_file = st.sidebar.file_uploader("📤 Upload Excel File", type=["xlsx"])
    if uploaded_file:
        upload_to_github(uploaded_file)

# --- File Dropdown ---
file_list = get_file_list()
def extract_date(filename):
    try:
        return datetime.strptime(re.findall(r"\d{2}\.\d{2}\.\d{4}", filename)[0], "%d.%m.%Y")
    except:
        return datetime.min

selected_file = st.selectbox("📁 Select Price File", file_list, index=0, format_func=lambda x: f"{x}")

# --- Load Data ---
data = load_data(selected_file)

# --- Dropdowns with persistence ---
if "model" not in st.session_state:
    st.session_state.model = ""
    st.session_state.fuel_type = ""
    st.session_state.variant = ""

models = sorted(data["Model"].dropna().unique())
if st.session_state.model not in models:
    st.session_state.model = models[0]

model = st.selectbox("🚘 Select Model", models, index=models.index(st.session_state.model))
st.session_state.model = model

fuel_df = data[data["Model"] == model]
fuel_types = sorted(fuel_df["Fuel Type"].dropna().unique())
if st.session_state.fuel_type not in fuel_types:
    st.session_state.fuel_type = fuel_types[0]

fuel_type = st.selectbox("⛽ Select Fuel Type", fuel_types, index=fuel_types.index(st.session_state.fuel_type))
st.session_state.fuel_type = fuel_type

variant_df = fuel_df[fuel_df["Fuel Type"] == fuel_type]
variant_options = sorted(variant_df["Variant"].dropna().unique())
if st.session_state.variant not in variant_options:
    st.session_state.variant = variant_options[0]

variant = st.selectbox("🎯 Select Variant", variant_options, index=variant_options.index(st.session_state.variant))
st.session_state.variant = variant

selected_row = variant_df[variant_df["Variant"] == variant]
if selected_row.empty:
    st.warning("⚠️ No data found for selected filters.")
    st.stop()

row = selected_row.iloc[0]

# --- Pricing Display (reuse your same formatter and table logic) ---
# Copy your format_indian_currency and render_combined_table functions here

# Then finally:
st.markdown(f"### 🚙 {model} - {fuel_type} - {variant}")
st.subheader("📋 Vehicle Pricing Details")
st.markdown(render_combined_table(row, shared_fields, grouped_fields, group_keys), unsafe_allow_html=True)
