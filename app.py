import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import base64
import re
from datetime import datetime

# ------------------- Configuration -------------------
st.set_page_config(page_title="Mahindra Vehicle Pricing Viewer", layout="wide")

ADMIN_PASSWORD = st.secrets["auth"]["admin_password"]
GITHUB_TOKEN = st.secrets["github"]["token"]
REPO = st.secrets["github"]["REPO"]
DATA_DIR = st.secrets["github"]["DATA_DIR"]

headers = {"Authorization": f"token {GITHUB_TOKEN}"}

# ------------------- Helper Functions -------------------
def list_files():
    api_url = f"https://api.github.com/repos/{REPO}/contents/{DATA_DIR}"
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()
    files = response.json()
    file_list = []
    for f in files:
        name = f["name"]
        match = re.search(r"(\d{2}\.\d{2}\.\d{4})", name)
        if match:
            dt = datetime.strptime(match.group(1), "%d.%m.%Y")
            file_list.append((dt, name))
    sorted_files = sorted(file_list, reverse=True)
    return [name for _, name in sorted_files[:5]]

def load_data(filename):
    raw_url = f"https://raw.githubusercontent.com/{REPO}/main/{DATA_DIR}/{filename}"
    response = requests.get(raw_url)
    response.raise_for_status()
    return pd.read_excel(BytesIO(response.content))

def upload_to_github(file, filename):
    content = file.read()
    b64_content = base64.b64encode(content).decode()
    api_url = f"https://api.github.com/repos/{REPO}/contents/{DATA_DIR}/{filename}"
    data = {
        "message": f"Upload {filename}",
        "content": b64_content,
        "branch": "main"
    }
    put_response = requests.put(api_url, headers=headers, json=data)
    if put_response.status_code in [200, 201]:
        return True
    else:
        st.error(f"Upload failed: {put_response.json()}")
        return False

# ------------------- Admin Login -------------------
with st.sidebar.expander("🔐 Admin Login", expanded=True):
    password = st.text_input("Enter admin password:", type="password")
    if st.button("Login"):
        if password == ADMIN_PASSWORD:
            st.session_state["is_admin"] = True
            st.success("Logged in as admin.")
        else:
            st.error("Incorrect password.")

# ------------------- Title -------------------
st.markdown("### 🚗 Mahindra Vehicle Pricing Viewer")

# ------------------- File Upload (Admin Only) -------------------
if st.session_state.get("is_admin"):
    with st.expander("⬆️ Upload New Price List"):
        uploaded_file = st.file_uploader("Choose Excel file", type=["xlsx"])
        if uploaded_file:
            filename = uploaded_file.name
            if st.button("Upload to GitHub"):
                success = upload_to_github(uploaded_file, filename)
                if success:
                    st.success(f"✅ Uploaded `{filename}` to GitHub")
                    st.rerun()

# ------------------- File Dropdown -------------------
file_list = list_files()
default_file = file_list[0] if file_list else None
selected_file = st.selectbox("📂 Select File", file_list, index=0, key="selected_file")

# ------------------- Load Data -------------------
if selected_file:
    df = load_data(selected_file)

    # Dropdown filters with state preservation
    col1, col2, col3 = st.columns(3)

    with col1:
        models = df["Model"].dropna().unique().tolist()
        previous_model = st.session_state.get("selected_model")
        default_model = previous_model if previous_model in models else models[0]
        model = st.selectbox("Model", models, index=models.index(default_model), key="selected_model")

    with col2:
        fuel_types = df[df["Model"] == model]["Fuel"].dropna().unique().tolist()
        previous_fuel = st.session_state.get("selected_fuel")
        default_fuel = previous_fuel if previous_fuel in fuel_types else fuel_types[0]
        fuel = st.selectbox("Fuel", fuel_types, index=fuel_types.index(default_fuel), key="selected_fuel")

    with col3:
        variants = df[(df["Model"] == model) & (df["Fuel"] == fuel)]["Variant"].dropna().unique().tolist()
        previous_variant = st.session_state.get("selected_variant")
        default_variant = previous_variant if previous_variant in variants else variants[0]
        variant = st.selectbox("Variant", variants, index=variants.index(default_variant), key="selected_variant")

    # ------------------- Display Filtered Data -------------------
    filtered = df[
        (df["Model"] == model) &
        (df["Fuel"] == fuel) &
        (df["Variant"] == variant)
    ]
    st.dataframe(filtered.reset_index(drop=True), use_container_width=True)
