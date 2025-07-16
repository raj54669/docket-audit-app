import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import re

# --- Page Configuration ---
st.set_page_config(
    page_title="Mahindra Pricing Viewer",
    layout="wide",  # Use full screen width
    initial_sidebar_state="auto"
)

# --- Remove Streamlit Header/Footer Padding ---
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Constants ---
FILE_PATH = "PV Price List Master D. 08.07.2025.xlsx"
SHARED_FIELDS = [
    "Ex-Showroom Price", "TCS 1%", "Insurance 1 Yr OD + 3 Yr TP + Zero Dep.",
    "Accessories Kit", "SMC", "Extended Warranty", "Maxi Care", "RSA (1 Year)", "Fastag"
]
GROUPED_FIELDS = [
    "RTO (W/O HYPO)", "RTO (With HYPO)",
    "On Road Price (W/O HYPO)", "On Road Price (With HYPO)"
]
GROUP_KEYS = {
    "RTO (W/O HYPO)": ("RTO (W/O HYPO) - Individual", "RTO (W/O HYPO) - Corporate"),
    "RTO (With HYPO)": ("RTO (With HYPO) - Individual", "RTO (With HYPO) - Corporate"),
    "On Road Price (W/O HYPO)": ("On Road Price (W/O HYPO) - Individual", "On Road Price (W/O HYPO) - Corporate"),
    "On Road Price (With HYPO)": ("On Road Price (With HYPO) - Individual", "On Road Price (With HYPO) - Corporate"),
}

# --- Table Styling ---
st.markdown("""
    <style>
    .table-wrapper { margin-bottom: 15px; padding: 0; }
    .styled-table {
        width: 100%; border-collapse: collapse;
        font-size: 16px; line-height: 1.2; border: 2px solid black;
    }
    .styled-table th, .styled-table td {
        border: 1px solid black; padding: 8px 10px; text-align: center;
    }
    .styled-table th { background-color: #004d40; color: white; font-weight: bold; }
    .styled-table td:first-child {
        text-align: left; font-weight: 600; background-color: #f7f7f7;
    }
    .table-wrapper + .table-wrapper { margin-top: -8px; }
    @media (prefers-color-scheme: dark) {
        .styled-table { border: 2px solid white; }
        .styled-table th, .styled-table td { border: 1px solid white; }
        .styled-table td { background-color: #111; color: #eee; }
        .styled-table td:first-child { background-color: #1e1e1e; color: white; }
    }
    </style>
""", unsafe_allow_html=True)


# --- Helper Functions ---
@st.cache_data(show_spinner=False)
def load_data(file_path: str) -> pd.DataFrame:
    if not os.path.exists(file_path):
        st.error("❌ Pricing file not found.")
        st.stop()
    try:
        return pd.read_excel(file_path)
    except Exception as e:
        st.error(f"❌ Failed to load Excel file: {e}")
        st.stop()

def format_indian_currency(value) -> str:
    if pd.isnull(value):
        return "<i style='color:gray;'>N/A</i>"
    try:
        value = float(value)
        is_negative = value < 0
        value = abs(value)
        s = str(int(value))
        last_three, other = s[-3:], s[:-3]
        if other:
            other = re.sub(r'(\d)(?=(\d{2})+$)', r'\1,', other)
            formatted = f"{other},{last_three}"
        else:
            formatted = last_three
        result = f"₹{formatted}"
        return f"<b>{'-' if is_negative else ''}{result}</b>"
    except Exception:
        return "<i style='color:red;'>Invalid</i>"

def render_shared_table(row: pd.Series, fields: list[str]) -> str:
    rows = "\n".join(
        f"<tr><td>{field}</td><td>{format_indian_currency(row.get(field))}</td></tr>"
        for field in fields
    )
    return f"""
    <div class="table-wrapper">
    <table class="styled-table">
        <tr><th>Description</th><th>Amount</th></tr>
        {rows}
    </table></div>
    """

def render_registration_table(row: pd.Series, groups: list[str], keys: dict) -> str:
    rows = "\n".join(
        f"<tr><td>{field}</td><td>{format_indian_currency(row.get(keys[field][0]))}</td><td>{format_indian_currency(row.get(keys[field][1]))}</td></tr>"
        for field in groups
    )
    return f"""
    <div class="table-wrapper">
    <table class="styled-table">
        <tr><th>Registration</th><th>Individual</th><th>Corporate</th></tr>
        {rows}
    </table></div>
    """


# --- App Title ---
st.title("🚗 Mahindra Vehicle Pricing Viewer")

# --- Load Data ---
price_data = load_data(FILE_PATH)

# --- Last Updated Timestamp ---
try:
    ist_time = datetime.fromtimestamp(os.path.getmtime(FILE_PATH)) + timedelta(hours=5, minutes=30)
    st.caption(f"📅 Data last updated on: {ist_time.strftime('%d-%b-%Y %I:%M %p')} (IST)")
except Exception as e:
    st.error(f"Error: {e}")
