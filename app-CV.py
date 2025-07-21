import streamlit as st
import pandas as pd
import requests
import base64
import os
from datetime import datetime

# --- CONFIG ---
REPO_OWNER = "raj54669"
REPO_NAME = "docket-audit-app"
REPO_DIR = "Data/Discount_Cheker"
GITHUB_API = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{REPO_DIR}"

# --- FUNCTIONS ---
def download_excel(filename):
    raw_url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/{REPO_DIR}/{filename}"
    df = pd.read_excel(raw_url)
    return df

# Example usage in your app
st.set_page_config(page_title="Mahindra Docket Audit Tool - CV", layout="wide")

st.markdown("### 📂 Select Discount Sheet")

# Simulated file list for dropdown (this should be replaced by GitHub API fetch)
file_list = [
    "CV Discount Check Master File 12.07.2025.xlsx",
    "CV Discount Check Master File 05.07.2025.xlsx"
]

selected_file = st.selectbox("", file_list, index=0)

# Load the file and show a basic preview (just to test)
try:
    df = download_excel(selected_file)
    st.success("Excel file loaded successfully!")
    st.dataframe(df.head())
except Exception as e:
    st.error("Failed to load Excel file. Check URL or format.")
    st.exception(e)
