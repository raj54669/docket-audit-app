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

# --- Page Configuration ---
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
                details = df.iloc[:, 0].fillna("").tolist()[2:]
                amounts = variant_df.iloc[0, 2:].tolist()

                # Ensure both lists are equal in length
                min_len = min(len(details), len(amounts))
                details = details[:min_len]
                amounts = amounts[:min_len]

                result_df = pd.DataFrame({
                    "Description": details,
                    "Amount": amounts
                })

                # Format as Indian currency
                def format_currency(x):
                    try:
                        x = float(x)
                        is_negative = x < 0
                        x = abs(int(x))
                        s = f"{x}"
                        last3 = s[-3:]
                        other = s[:-3]
                        if other:
                            other = re.sub(r'(\d)(?=(\d{2})+$)', r'\1,', other)
                            formatted = f"{other},{last3}"
                        else:
                            formatted = last3
                        return f"₹{'-' if is_negative else ''}{formatted}"
                    except:
                        return x

                result_df["Amount"] = result_df["Amount"].apply(format_currency)

                # Styled Table Output
                st.markdown("""
                <style>
                .styled-table {
                    width: 80%;
                    border-collapse: collapse;
                    font-size: 15px;
                }
                .styled-table th {
                    background-color: #004d40;
                    color: white;
                    padding: 10px;
                    text-align: left;
                }
                .styled-table td {
                    padding: 8px 12px;
                    border-bottom: 1px solid #ccc;
                }
                .styled-table td:first-child {
                    font-weight: 600;
                    background-color: #f7f7f7;
                }
                @media (prefers-color-scheme: dark) {
                    .styled-table td {
                        background-color: #111;
                        color: #eee;
                    }
                    .styled-table td:first-child {
                        background-color: #1e1e1e;
                    }
                    .styled-table th {
                        background-color: #0e7c7b;
                    }
                }
                </style>
                <table class="styled-table">
                    <thead><tr><th>Description</th><th>Amount</th></tr></thead>
                    <tbody>
                """, unsafe_allow_html=True)

                for _, row in result_df.iterrows():
                    highlight = " style='background-color:#fff3cd;font-weight:bold;'" if "On Road Price" in row["Description"] else ""
                    st.markdown(f"<tr{highlight}><td>{row['Description']}</td><td>{row['Amount']}</td></tr>", unsafe_allow_html=True)

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
