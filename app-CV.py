import streamlit as st
import pandas as pd
import os
import requests
from urllib.parse import quote
from datetime import datetime

# --- Page config ---
st.set_page_config(page_title="Mahindra Docket Audit Tool - CV", layout="wide")

# --- Constants ---
REPO_OWNER = "raj54669"
REPO_NAME = "docket-audit-app"
REPO_DIR = "Data/Discount_Cheker"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/{REPO_DIR}"

# --- GitHub Token (from Secrets) ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

# --- Title ---
st.markdown("""
<h1 style='font-size: 32px;'>📁 Select Discount Sheet</h1>
""", unsafe_allow_html=True)

# --- Fetch file list from GitHub ---
def list_repo_files():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{REPO_DIR}"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        files = [f["name"] for f in res.json() if f["name"].endswith(".xlsx")]
        return sorted(files, reverse=True)
    else:
        return []

# --- Read Excel file from GitHub ---
def download_excel(filename):
    try:
        encoded_filename = quote(filename)
        raw_url = f"{RAW_BASE}/{encoded_filename}"
        df = pd.read_excel(raw_url, engine="openpyxl")
        return df
    except Exception as e:
        st.error("Failed to load Excel file. Check URL or format.")
        st.exception(e)
        return None

# --- Format Indian Currency ---
def format_inr(value):
    try:
        return f"₹{int(value):,}".replace(",", ",").replace(",", ",")
    except:
        return value

# --- App Logic ---
file_list = list_repo_files()
selected_file = st.selectbox("", file_list, index=0, key="file_select")
df_raw = download_excel(selected_file)

if df_raw is not None:
    # --- Extract variant list ---
    variant_col = "Variant"
    variant_options = df_raw[variant_col].dropna().unique().tolist()
    selected_variant = st.selectbox("Select Variant", variant_options, index=0)

    # --- Filtered Data ---
    filtered_df = df_raw[df_raw[variant_col] == selected_variant]

    if not filtered_df.empty:
        # --- Split data ---
        pricing_cols = filtered_df.columns[:filtered_df.columns.get_loc("On Road Price") + 1]
        cartel_cols = filtered_df.columns[-3:]

        pricing_df = filtered_df[pricing_cols].drop(columns=["Model Name"], errors="ignore")
        cartel_df = filtered_df[cartel_cols]

        # --- Format currency columns ---
        for col in pricing_df.columns:
            if pd.api.types.is_numeric_dtype(pricing_df[col]):
                pricing_df[col] = pricing_df[col].apply(format_inr)

        # --- Display Tables ---
        st.subheader("Vehicle Pricing Data")
        st.dataframe(pricing_df, use_container_width=True, hide_index=True)

        st.subheader("Cartel Offer")
        st.dataframe(cartel_df.astype(str), use_container_width=True, hide_index=True)
    else:
        st.warning("No data found for the selected variant.")
else:
    st.error("Unable to load file. Please check your internet or file source.")
