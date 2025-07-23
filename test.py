import streamlit as st
import os
import base64
import datetime
import pandas as pd
from github import Github

# --- Page Configuration ---
st.set_page_config(page_title="Mahindra Vehicle Pricing Viewer", page_icon="🚗", layout="wide")

# --- Top Padding Restore ---
st.markdown(
    """
    <style>
    .main > div:first-child {
        padding-top: 3rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Authentication ---
def admin_login():
    with st.sidebar:
        st.markdown("### 🔐 Admin Login")
        password = st.text_input("Enter Admin Password", type="password")
        if password:
            if "auth" in st.secrets and st.secrets["auth"].get("admin_password") == password:
                st.success("Admin authenticated")
                return True
            else:
                st.error("Incorrect password")
    return False

# --- GitHub Setup ---
@st.cache_resource
def connect_github():
    access_token = st.secrets["github"]["access_token"]
    repo_name = "raj54669/docket-audit-app"
    g = Github(access_token)
    repo = g.get_repo(repo_name)
    return repo

# --- Utility: Get recent pricing files ---
def get_recent_files(repo, folder="Data/Price_List"):
    contents = repo.get_contents(folder)
    files = [f for f in contents if f.name.endswith(".xlsx")]
    sorted_files = sorted(
        files,
        key=lambda f: datetime.datetime.strptime(f.name.split(" D. ")[-1].replace(".xlsx", ""), "%d.%m.%Y"),
        reverse=True
    )
    return sorted_files[:5]

# --- Utility: Load Excel from GitHub ---
@st.cache_data(show_spinner=False)
def load_excel_file(file_content):
    return pd.read_excel(file_content)

# --- Main App ---
def main():
    st.markdown("<h1 style='text-align: center;'>🚗 Mahindra Vehicle Pricing Viewer</h1>", unsafe_allow_html=True)

    repo = connect_github()
    recent_files = get_recent_files(repo)

    file_names = [f.name for f in recent_files]
    default_index = 0  # most recent file is first

    selected_file_name = st.selectbox("Select Price List File", file_names, index=default_index)
    selected_file = next(f for f in recent_files if f.name == selected_file_name)
    excel_bytes = selected_file.decoded_content
    df = load_excel_file(excel_bytes)

    # --- Dropdowns ---
    model_options = sorted(df['Model'].dropna().unique())
    model = st.selectbox("Select Model", model_options, key="model")

    fuel_options = sorted(df[df['Model'] == model]['Fuel Type'].dropna().unique())
    fuel = st.selectbox("Select Fuel Type", fuel_options, key="fuel")

    variant_options = sorted(df[(df['Model'] == model) & (df['Fuel Type'] == fuel)]['Variant'].dropna().unique())
    variant = st.selectbox("Select Variant", variant_options, key="variant")

    # --- Show Filtered Data ---
    filtered_df = df[(df['Model'] == model) & (df['Fuel Type'] == fuel) & (df['Variant'] == variant)]
    st.write("### Price Details")
    st.dataframe(filtered_df)

    # --- Admin Upload Feature ---
    if admin_login():
        st.write("---")
        st.markdown("### 📤 Upload New Price List")
        uploaded_file = st.file_uploader("Upload .xlsx File", type=["xlsx"])
        if uploaded_file:
            upload_path = f"Data/Price_List/{uploaded_file.name}"
            repo.create_file(
                path=upload_path,
                message=f"Uploaded {uploaded_file.name}",
                content=uploaded_file.read(),
                branch="main"
            )
            st.success(f"Uploaded {uploaded_file.name} to GitHub.")

if __name__ == "__main__":
    main()
