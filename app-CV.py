import streamlit as st
import pandas as pd
import os
import re
import requests
from datetime import datetime

# --- Config ---
REPO = "raj54669/docket-audit-app"
REPO_DIR = "Data/Discount_Cheker"
GITHUB_API = f"https://api.github.com/repos/{REPO}/contents/{REPO_DIR}"
HEADERS = {"Authorization": f"Bearer {st.secrets['github_token']}"}

# --- Page Setup ---
st.set_page_config("Mahindra Docket Audit Tool - CV", layout="centered")
st.markdown("""
    <style>
    html, body, [class^="st"] {
        font-family: 'Segoe UI', sans-serif;
    }
    @media (prefers-color-scheme: dark) {
        .styled-table th, .styled-table td { border: 1px solid white; }
        .styled-table td { background-color: #111; color: #eee; }
        .styled-table td:first-child { background-color: #1e1e1e; color: white; }
    }
    </style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def parse_date_from_filename(name):
    match = re.search(r"(\d{2})[.-](\d{2})[.-](\d{4})", name)
    if match:
        return datetime.strptime(".".join(match.groups()), "%d.%m.%Y")
    return None

def get_latest_files():
    res = requests.get(GITHUB_API, headers=HEADERS)
    res.raise_for_status()
    files = res.json()
    excel_files = [f for f in files if f["name"].endswith(".xlsx")]
    dated_files = [(f["name"], parse_date_from_filename(f["name"])) for f in excel_files]
    dated_files = [f for f in dated_files if f[1] is not None]
    sorted_files = sorted(dated_files, key=lambda x: x[1], reverse=True)
    return [f[0] for f in sorted_files[:5]]

def download_excel(filename):
    raw_url = f"https://raw.githubusercontent.com/{REPO}/main/{REPO_DIR}/{filename}"
    df = pd.read_excel(raw_url)
    return df

def format_currency(val):
    try:
        val = float(val)
        is_neg = val < 0
        val = abs(int(val))
        s = str(val)
        if len(s) > 3:
            s = s[:-3][::-1]
            s = ",".join([s[i:i+2] for i in range(0, len(s), 2)])[::-1] + "," + str(val)[-3:]
        else:
            s = str(val)
        return f"{'-' if is_neg else ''}₹{s}"
    except:
        return "-"

def render_table(df, numeric_cols):
    styled = df.copy()
    for col in numeric_cols:
        if col in styled.columns:
            styled[col] = styled[col].apply(format_currency)
    st.markdown("""
    <style>
    .styled-table {
        width: 100%; border-collapse: collapse; margin: 10px 0;
        font-size: 14px; line-height: 1.2; border: 2px solid black;
    }
    .styled-table th, .styled-table td {
        border: 1px solid black; padding: 6px 8px; text-align: center;
    }
    .styled-table td:first-child { text-align: left; font-weight: bold; }
    .styled-table th { background-color: #004d40; color: white; }
    </style>
    """, unsafe_allow_html=True)
    st.write(styled.to_html(index=False, classes="styled-table"), unsafe_allow_html=True)

# --- Title ---
st.title("📊 Mahindra Docket Audit Tool - CV")

# --- File Dropdown ---
files = get_latest_files()
if not files:
    st.error("No data files found in repository.")
    st.stop()

selected_file = st.selectbox("📁 Select Discount Sheet", options=files, index=0)
df = download_excel(selected_file)

if df.empty or "Variant" not in df.columns:
    st.error("Invalid or empty Excel file.")
    st.stop()

# --- Variant Selector ---
variants = sorted(df["Variant"].dropna().unique())
variant = st.selectbox("🚘 Select Variant", variants)
filtered = df[df["Variant"] == variant]
if filtered.empty:
    st.warning("No data for selected variant.")
    st.stop()

row = filtered.iloc[0]

# --- Table 1: Vehicle Pricing Data (first 12 columns except Model Name) ---
st.subheader("💰 Vehicle Pricing Data")
pricing_df = pd.DataFrame([row.iloc[1:12]]).copy()  # Skip Model Name
render_table(pricing_df, numeric_cols=pricing_df.columns.tolist())

# --- Table 2: Cartel Offer (last 3 columns) ---
st.subheader("🎁 Cartel Offer")
offer_cols = df.columns[-3:]
offer_df = pd.DataFrame([row[offer_cols]]).copy()
render_table(offer_df, numeric_cols=offer_df.columns[:1].tolist())  # Only first column is numeric

# --- Admin Upload Section ---
with st.expander("🔒 Admin Login"):
    pw = st.text_input("Enter Admin Password", type="password")
    if pw == st.secrets["admin_password"]:
        upload = st.file_uploader("📤 Upload New Discount Sheet", type="xlsx")
        if upload:
            uploaded_bytes = upload.read()
            filename = upload.name

            # Push to GitHub via API
            res = requests.put(
                f"{GITHUB_API}/{filename}",
                headers=HEADERS,
                json={
                    "message": f"Upload {filename}",
                    "content": uploaded_bytes.encode("base64"),
                    "branch": "main"
                },
            )
            if res.status_code in [200, 201]:
                st.success("✅ File uploaded to GitHub successfully.")
                st.rerun()
            else:
                st.error("❌ Upload failed. Check GitHub token and permissions.")
    elif pw:
        st.error("❌ Incorrect password")
