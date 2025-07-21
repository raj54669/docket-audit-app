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

            # --- Extract variants ---
            variant_col = df.columns[1]
            variants = df[variant_col].dropna().unique().tolist()
            selected_variant = st.selectbox("Select Variant", variants)

            # --- Extract vertical data for selected variant ---
            variant_df = df[df[variant_col] == selected_variant]
            if not variant_df.empty:
                details = df.iloc[:, 0].fillna("").tolist()
                amounts = variant_df.iloc[0, 2:].tolist()

                result_df = pd.DataFrame({
                    "Description": details[2:],
                    "Amount": amounts
                })

                # --- Format amounts ---
                def format_currency(x):
                    try:
                        return f"₹{int(x):,}"
                    except:
                        return x

                result_df["Amount"] = result_df["Amount"].apply(format_currency)

                # --- Styled Table ---
                st.markdown("""
                <h4>📑 Vehicle Pricing Details</h4>
                <style>
                .pricing-table {
                    width: 60%;
                    border-collapse: collapse;
                    margin: 10px 0;
                }
                .pricing-table th {
                    background-color: #0c4a6e;
                    color: white;
                    padding: 10px;
                    text-align: left;
                }
                .pricing-table td {
                    padding: 8px 12px;
                    border-bottom: 1px solid #ccc;
                }
                .highlight {
                    background-color: #fef3c7;
                }
                </style>
                <table class="pricing-table">
                    <thead>
                        <tr><th>Description</th><th>Amount</th></tr>
                    </thead>
                    <tbody>
                """, unsafe_allow_html=True)

                for i, row in result_df.iterrows():
                    highlight_class = "highlight" if "On Road Price" in row["Description"] else ""
                    st.markdown(f"<tr class='{highlight_class}'><td>{row['Description']}</td><td>{row['Amount']}</td></tr>", unsafe_allow_html=True)

                st.markdown("""</tbody></table>""", unsafe_allow_html=True)
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
