import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime
from io import BytesIO

# --- Config ---
OWNER = "raj54669"
REPO = "docket-audit-app"
PATH = "Data/Discount_Cheker"

# --- GitHub Token (from Secrets) ---
GITHUB_TOKEN = st.secrets["github_token"]
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

# --- Title ---
st.set_page_config(page_title="Mahindra Docket Audit Tool - CV", layout="wide")
st.title("Mahindra Docket Audit Tool - CV")

# --- Helper: List files from repo ---
def list_files():
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{PATH}"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        files = [f['name'] for f in res.json() if f['name'].endswith('.xlsx')]
        return sorted(files, reverse=True)
    else:
        st.error("Failed to fetch files from GitHub")
        return []

# --- Helper: Upload new file ---
def upload_file_to_github(file, filename):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{PATH}/{filename}"
    content = base64.b64encode(file.read()).decode('utf-8')
    data = {
        "message": f"Upload {filename}",
        "content": content
    }
    res = requests.put(url, headers=HEADERS, json=data)
    if res.status_code == 201:
        st.success(f"Uploaded: {filename}")
    elif res.status_code == 422 and "already exists" in res.text:
        st.warning(f"Duplicate: {filename} already exists")
    else:
        st.error(f"Upload failed: {res.status_code}")

# --- Helper: Delete a file from GitHub ---
def delete_file_from_github(filename):
    get_url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{PATH}/{filename}"
    res = requests.get(get_url, headers=HEADERS)
    if res.status_code == 200:
        sha = res.json()['sha']
        delete_url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{PATH}/{filename}"
        data = {
            "message": f"Delete {filename}",
            "sha": sha
        }
        res = requests.delete(delete_url, headers=HEADERS, json=data)
        if res.status_code == 200:
            st.success(f"Deleted old file: {filename}")
        else:
            st.error(f"Failed to delete {filename}")

# --- Upload File Section ---
uploaded_file = st.file_uploader("Upload new Excel file", type="xlsx")
if uploaded_file:
    filename = uploaded_file.name
    file_list = list_files()
    if filename not in file_list:
        upload_file_to_github(uploaded_file, filename)
        file_list = list_files()
        if len(file_list) > 5:
            for old_file in sorted(file_list)[0:len(file_list)-5]:
                delete_file_from_github(old_file)
    else:
        st.warning("This file already exists in the repository.")

# --- Dropdown to select file ---
file_list = list_files()
if file_list:
    selected_file = st.selectbox("Select a file to view", file_list, index=0)
    if selected_file:
        api_url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{PATH}/{selected_file}"
        res = requests.get(api_url, headers=HEADERS)
        if res.status_code == 200:
            file_content = base64.b64decode(res.json()['content'])
            df = pd.read_excel(BytesIO(file_content))
            st.write(f"### Showing data from: {selected_file}")
            st.dataframe(df, use_container_width=True)
        else:
            st.error("Failed to download the selected file from GitHub")

# --- Auto Light/Dark Mode Styling ---
st.markdown("""
    <style>
        body {
            transition: background-color 0.5s ease;
        }
        [data-theme="light"] body {
            background-color: #ffffff;
            color: #000000;
        }
        [data-theme="dark"] body {
            background-color: #0e1117;
            color: #ffffff;
        }
    </style>
""", unsafe_allow_html=True)
