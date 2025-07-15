import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- GitHub File Commit Timestamp ---
GITHUB_REPO = "nishaldev/mahindra-pricing"  # 🛠️ Replace with your actual repo name
FILE_PATH = "data/PV Price List Master D. 08.07.2025.xlsx"  # 🛠️ Exact path in your repo

def get_last_updated(repo, file_path):
    url = f"https://api.github.com/repos/{repo}/commits?path={file_path}"
    response = requests.get(url)
    if response.status_code == 200 and response.json():
        commit_date = response.json()[0]["commit"]["committer"]["date"]
        dt = datetime.strptime(commit_date, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime("%d %B %Y, %I:%M %p")
    return "Unknown"

# --- Load Pricing Data ---
@st.cache_data
def load_price_data():
    return pd.read_excel("PV Price List Master D. 08.07.2025.xlsx")

price_data = load_price_data()

# --- Page Setup ---
st.set_page_config(page_title="Mahindra Pricing Viewer", layout="centered")
st.title("🚗 Mahindra Vehicle Pricing Viewer")

# --- Sidebar Info ---
last_updated = get_last_updated(GITHUB_REPO, FILE_PATH)
with st.sidebar:
    st.markdown(f"🕒 **Last Updated On GitHub:** {last_updated}")
    if st.button("🔄 Refresh App"):
        st.rerun()

# --- Step 1: Select Model ---
model = st.selectbox("Select Model", sorted(price_data["Model"].unique()))

# --- Step 2: Select Fuel Type ---
fuel_options = price_data[price_data["Model"] == model]["Fuel Type"].unique()
