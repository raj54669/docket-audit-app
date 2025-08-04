import streamlit as st
import pandas as pd
import os
import re
import base64
import requests
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="🚗 Mahindra Vehicle Pricing Viewer",
    layout="centered",
    initial_sidebar_state="auto"
)

# --- Constants ---
DATA_DIR = "Data/Price_List"
FILE_PATTERN = r"PV Price List Master D\. (\d{2})\.(\d{2})\.(\d{4})\.xlsx"

# --- Global Styling ---
st.markdown("""
<style>
:root {
    --title-size: 40px;
    --subtitle-size: 20px;
    --caption-size: 16px;
    --label-size: 14px;
    --select-font-size: 15px;
    --table-font-size: 14px;
    --variant-title-size: 24px;
}
.block-container { padding-top: 0rem; }
header {visibility: hidden;}
h1 { font-size: var(--title-size) !important; }
h2 { font-size: var(--subtitle-size) !important; }
h3 { font-size: var(--variant-title-size) !important; }
.stCaption { font-size: var(--caption-size) !important; }
.stSelectbox label { font-size: var(--label-size) !important; font-weight: 600 !important; }
.stSelectbox div[data-baseweb="select"] > div {
    font-size: var(--select-font-size) !important;
    font-weight: bold !important;
    padding-top: 2px !important;
    padding-bottom: 2px !important;
    line-height: 1 !important;
    min-height: 24px !important;
}
.stSelectbox div[data-baseweb="select"] { align-items: center !important; height: 28px !important; }
.stSelectbox [data-baseweb="menu"] > div { padding-top: 2px !important; padding-bottom: 2px !important; }
.stSelectbox [data-baseweb="option"] {
    padding: 4px 10px !important;
    font-size: var(--select-font-size) !important;
    font-weight: 500 !important;
    line-height: 1.2 !important;
    min-height: 28px !important;
}
.stSelectbox [data-baseweb="option"]:hover {
    background-color: #f0f0f0 !important;
    font-weight: 600 !important;
}
.table-wrapper { margin-bottom: 15px; padding: 0; }
.styled-table {
    width: 100%; border-collapse: collapse; table-layout: fixed;
    font-size: var(--table-font-size); line-height: 1.2; border: 2px solid black;
}
.styled-table th, .styled-table td {
    border: 1px solid black; padding: 4px 6px; text-align: center; line-height: 1.2;
}
.styled-table th:nth-child(1), .styled-table td:nth-child(1) {
    width: 60%;
}
.styled-table th:nth-child(2), .styled-table td:nth-child(2),
.styled-table th:nth-child(3), .styled-table td:nth-child(3) {
    width: 20%;
}
.styled-table th { background-color: #004d40; color: white; font-weight: bold; }
.styled-table td:first-child {
    text-align: left; font-weight: 600; background-color: #f7f7f7;
}
@media (prefers-color-scheme: dark) {
    .styled-table { border: 2px solid white; }
    .styled-table th, .styled-table td { border: 1px solid white; }
    .styled-table td { background-color: #111; color: #eee; }
    .styled-table td:first-child { background-color: #1e1e1e; color: white; }
}
</style>
""", unsafe_allow_html=True)

# --- Admin Auth ---
def check_admin_password():
    correct_password = st.secrets["auth"]["admin_password"]
    if "admin_authenticated" not in st.session_state:
        st.session_state["admin_authenticated"] = False

    if not st.session_state["admin_authenticated"]:
        with st.sidebar.expander("🔐 Admin Login", expanded=True):
            pwd = st.text_input("Enter admin password:", type="password", key="admin_pwd")
            if st.button("Login", key="admin_login_btn"):
                if pwd == correct_password:
                    st.session_state["admin_authenticated"] = True
                    st.rerun()
                else:
                    st.error("❌ Incorrect password.")
        return False
    return True

def logout_admin():
    if st.session_state.get("admin_authenticated", False):
        if st.sidebar.button("🔓 Logout Admin"):
            st.session_state["admin_authenticated"] = False
            st.rerun()

# --- GitHub Upload Logic ---
def upload_to_github(uploaded_file):
    token = st.secrets["github"]["token"]
    username = st.secrets["github"]["username"]
    repo = st.secrets["github"]["repo"]
    branch = st.secrets["github"].get("branch", "main")
    github_dir = DATA_DIR

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    github_path = f"{github_dir}/{uploaded_file.name}"
    content = base64.b64encode(uploaded_file.getbuffer()).decode()

    url = f"https://api.github.com/repos/{username}/{repo}/contents/{github_path}"
    check = requests.get(url, headers=headers)
    sha = check.json().get("sha") if check.status_code == 200 else None

    payload = {
        "message": f"Upload {uploaded_file.name}",
        "content": content,
        "branch": branch
    }
    if sha:
        payload["sha"] = sha

    r = requests.put(url, headers=headers, json=payload)
    if r.status_code in [200, 201]:
        st.sidebar.success("✅ Uploaded successfully")
    else:
        st.sidebar.error("❌ Upload failed")

# --- Sidebar Upload ---
if check_admin_password():
    st.sidebar.header("📂 File Upload (Admin Only)")
    file = st.sidebar.file_uploader("Upload New Excel File", type=["xlsx"])
    if file:
        upload_to_github(file)
        st.rerun()
logout_admin()

# --- Title ---
st.title("🚗 Mahindra Vehicle Pricing Viewer")

# --- File Listing ---
def extract_date_from_filename(filename):
    match = re.match(FILE_PATTERN, filename)
    if match:
        try:
            return datetime.strptime(".".join(match.groups()), "%d.%m.%Y")
        except:
            return None
    return None

def list_recent_files():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    all_files = os.listdir(DATA_DIR)
    valid = [(f, extract_date_from_filename(f)) for f in all_files if re.match(FILE_PATTERN, f)]
    return sorted([f for f in valid if f[1]], key=lambda x: x[1], reverse=True)[:5]

files = list_recent_files()
if not files:
    st.error("❌ No valid Excel files found")
    st.stop()

file_labels = [f"{name} ({dt.strftime('%d-%b-%Y')})" for name, dt in files]
file_map = {label: name for label, (name, _) in zip(file_labels, files)}

selected_label = st.selectbox("📅 Select Excel File", file_labels, key="main_excel_file")
selected_path = os.path.join(DATA_DIR, file_map[selected_label])

# --- Category Selection FIRST ---
col1, col2 = st.columns([1, 3])
with col1:
    category = st.selectbox("🔍 Category", ["PV", "EV"], index=0)

# --- Data Loader ---
@st.cache_data(show_spinner=False)
def load_data(file_path, sheet_name):
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    df.columns = df.columns.str.strip()
    return df

df = load_data(selected_path, sheet_name=category)

# --- Dropdown State Logic ---
def safe_selectbox(label, options, session_key):
    selected = st.session_state.get(session_key)
    if selected not in options:
        selected = options[0] if options else None
    return st.selectbox(label, options, index=options.index(selected) if selected in options else 0, key=session_key)

# --- Dynamic Dropdowns ---
models = sorted(df["Model"].dropna().unique())
if not models:
    st.error("❌ No models found")
    st.stop()

with col2:
    model = safe_selectbox("🚘 Model", models, "selected_model")

variant_df = df[df["Model"] == model]

if "Variant" not in variant_df.columns:
    st.error("❌ 'Variant' column is missing in the selected category sheet.")
    st.stop()
variants = sorted(variant_df["Variant"].dropna().unique())

variant = safe_selectbox("🎯 Select Variant", variants, "selected_variant")
filtered_rows = variant_df[variant_df["Variant"] == variant]

if filtered_rows.empty:
    st.warning("⚠️ No data available for this variant.")
    st.stop()

row = filtered_rows.iloc[0]

# --- Format Currency ---
def format_indian_currency(value):
    try:
        if pd.isnull(value): return "<i style='color:gray;'>N/A</i>"
        value = float(value)
        is_negative = value < 0
        value = abs(value)
        s = f"{int(value)}"
        last_three = s[-3:]
        other = s[:-3]
        if other:
            other = re.sub(r'(\d)(?=(\d{2})+$)', r'\1,', other)
            formatted = f"{other},{last_three}"
        else:
            formatted = last_three
        result = f"₹{formatted}"
        return f"<b>{'-' if is_negative else ''}{result}</b>"
    except:
        return "<i style='color:red;'>Invalid</i>"

# --- Table Renderer ---
def render_combined_table(row, shared_fields, grouped_fields, group_keys):
    html = """
    <style>
    .vtable { border-collapse: collapse; width: 100%; font-weight: bold; font-size: 14px; }
    .vtable th { background-color: #004080; color: white; padding: 4px 6px; text-align: center; }
    .vtable td { background-color: #f0f4f8; padding: 4px 6px; text-align: center; color: black; font-weight: bold }
    .vtable td:first-child, .vtable th:first-child { text-align: left; }
    .vtable, .vtable th, .vtable td { border: 1px solid #000; }
    </style>
    <table class='vtable'>
        <tr><th>Description</th><th>Individual</th><th>Corporate</th></tr>
    """

    for field in shared_fields:
        val = format_indian_currency(row.get(field))
        if "N/A" not in val and "Invalid" not in val:
            html += f"<tr><td>{field}</td><td>{val}</td><td>{val}</td></tr>"
            
    for field in grouped_fields:
        ind_key, corp_key = group_keys.get(field, ("", ""))
        ind_val = format_indian_currency(row.get(ind_key))
        corp_val = format_indian_currency(row.get(corp_key))
        html += f"<tr><td>{field}</td><td>{ind_val}</td><td>{corp_val}</td></tr>"

    html += "</table>"
    return html

# --- Output ---
st.markdown(f"<h2 style='margin-top: -8px; '> 🚙 {model} - {variant}</h2>", unsafe_allow_html=True)
st.markdown("<h3 style='color:#e65100; margin-top: -10px; margin-bottom: -8px;'>📝 Vehicle Pricing Details</h3>", unsafe_allow_html=True)

available_columns = df.columns

shared_fields_all = [
    "Ex-Showroom Price", "TCS 1%", "Insurance 1 Yr OD + 3 Yr TP + Zero Dep.",
    "Accessories Kit", "SMC", "Extended Warranty", "Maxi Care", "RSA (1 Year)", "Fastag"
]
shared_fields = [f for f in shared_fields_all if f in available_columns]

group_keys_master = {
    "RTO (W/O HYPO)": ("RTO (W/O HYPO) - Individual", "RTO (W/O HYPO) - Corporate"),
    "RTO (With HYPO)": ("RTO (With HYPO) - Individual", "RTO (With HYPO) - Corporate"),
    "On Road Price (W/O HYPO)": ("On Road Price (W/O HYPO) - Individual", "On Road Price (W/O HYPO) - Corporate"),
    "On Road Price (With HYPO)": ("On Road Price (With HYPO) - Individual", "On Road Price (With HYPO) - Corporate"),
}

grouped_fields = []
group_keys = {}
for field, (ind_col, corp_col) in group_keys_master.items():
    if ind_col in available_columns and corp_col in available_columns:
        grouped_fields.append(field)
        group_keys[field] = (ind_col, corp_col)

if not any(col in row for col in shared_fields + [v for pair in group_keys.values() for v in pair]):
    st.warning("⚠️ No pricing details available for this variant.")
else:
    st.markdown(render_combined_table(row, shared_fields, grouped_fields, group_keys), unsafe_allow_html=True)
