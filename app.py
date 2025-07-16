import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tempfile

# --- Page Configuration ---
st.set_page_config(
    page_title="Mahindra Pricing Viewer",
    layout="centered",
    initial_sidebar_state="auto"
)

# --- Load Excel Data ---
@st.cache_data
def load_data():
    try:
        return pd.read_excel("PV Price List Master D. 08.07.2025.xlsx")
    except FileNotFoundError:
        st.error("❌ Pricing file not found.")
        st.stop()

price_data = load_data()
file_path = "PV Price List Master D. 08.07.2025.xlsx"

# --- Currency Formatter (Indian style) ---
def format_indian_currency(value):
    import re
    if pd.isnull(value):
        return "<i style='color:gray;'>N/A</i>"
    try:
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
            formatted = f"{last_three}"
        result = f"₹{formatted}"
        return f"<b>{'-' if is_negative else ''}{result}</b>"
    except:
        return "<i style='color:red;'>Invalid</i>"

# --- Table Generators ---
def render_shared_table(row, fields):
    html = """
    <div class="table-wrapper">
    <table class="styled-table">
        <tr><th>Description</th><th>Amount</th></tr>
    """
    for field in fields:
        html += f"<tr><td>{field}</td><td>{format_indian_currency(row.get(field))}</td></tr>"
    html += "</table></div>"
    return html

def render_registration_table(row, groups, keys):
    html = """
    <div class="table-wrapper">
    <table class="styled-table">
        <tr><th>Registration</th><th>Individual</th><th>Corporate</th></tr>
    """
    for field in groups:
        ind_key, corp_key = keys[field]
        html += f"<tr><td>{field}</td><td>{format_indian_currency(row.get(ind_key))}</td><td>{format_indian_currency(row.get(corp_key))}</td></tr>"
    html += "</table></div>"
    return html

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
    @media (prefers-color-scheme: dark) {
        .styled-table { border: 2px solid white; }
        .styled-table th, .styled-table td { border: 1px solid white; }
        .styled-table td { background-color: #111; color: #eee; }
        .styled-table td:first-child { background-color: #1e1e1e; color: white; }
    }
    </style>
""", unsafe_allow_html=True)

# --- Title ---
st.title("🚗 Mahindra Vehicle Pricing Viewer")

# --- Timestamp ---
if os.path.exists(file_path):
    ist_time = datetime.fromtimestamp(os.path.getmtime(file_path)) + timedelta(hours=5, minutes=30)
    st.caption(f"📅 Data last updated on: {ist_time.strftime('%d-%b-%Y %I:%M %p')} (IST)")

# --- Dropdowns ---
models = sorted(price_data["Model"].dropna().unique())
model = st.selectbox("Select Model", models)

fuel_types = sorted(price_data[price_data["Model"] == model]["Fuel Type"].dropna().unique())
fuel_type = st.selectbox("Select Fuel Type", fuel_types)

# Filter variant options using text_input for searchable dropdown
variant_options = sorted(price_data[(price_data["Model"] == model) & (price_data["Fuel Type"] == fuel_type)]["Variant"].dropna().unique())
variant_search = st.text_input("Type to search Variant")
filtered_variants = [v for v in variant_options if variant_search.lower() in v.lower()]
variant = st.selectbox("Select Variant", filtered_variants if filtered_variants else variant_options)

selected_row = price_data[(price_data["Model"] == model) & (price_data["Fuel Type"] == fuel_type) & (price_data["Variant"] == variant)]

if selected_row.empty:
    st.warning("No data found for selected filters.")
    st.stop()

row = selected_row.iloc[0]
shared_fields = [
    "Ex-Showroom Price", "TCS 1%", "Insurance 1 Yr OD + 3 Yr TP + Zero Dep.",
    "Accessories Kit", "SMC", "Extended Warranty", "Maxi Care", "RSA (1 Year)", "Fastag"
]
grouped_fields = [
    "RTO (W/O HYPO)", "RTO (With HYPO)",
    "On Road Price (W/O HYPO)", "On Road Price (With HYPO)"
]
group_keys = {
    "RTO (W/O HYPO)": ("RTO (W/O HYPO) - Individual", "RTO (W/O HYPO) - Corporate"),
    "RTO (With HYPO)": ("RTO (With HYPO) - Individual", "RTO (With HYPO) - Corporate"),
    "On Road Price (W/O HYPO)": ("On Road Price (W/O HYPO) - Individual", "On Road Price (W/O HYPO) - Corporate"),
    "On Road Price (With HYPO)": ("On Road Price (With HYPO) - Individual", "On Road Price (With HYPO) - Corporate"),
}

st.subheader("📋 Vehicle Pricing Details")
st.markdown(render_shared_table(row, shared_fields), unsafe_allow_html=True)
st.markdown(render_registration_table(row, grouped_fields, group_keys), unsafe_allow_html=True)

# --- PDF Download using reportlab ---
def generate_pdf(row):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        c = canvas.Canvas(tmp.name, pagesize=letter)
        width, height = letter
        y = height - 40

        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, y, f"Mahindra Pricing - {model} / {variant} ({fuel_type})")
        y -= 30

        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Shared Costs")
        y -= 20
        c.setFont("Helvetica", 10)
        for field in shared_fields:
            val = row.get(field)
            text = f"{field}: ₹{int(val):,}" if pd.notnull(val) else f"{field}: N/A"
            c.drawString(50, y, text)
            y -= 14

        y -= 10
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Registration Costs")
        y -= 20
        c.setFont("Helvetica", 10)
        for field in grouped_fields:
            ind_key, corp_key = group_keys[field]
            ind_val = row.get(ind_key)
            corp_val = row.get(corp_key)
            text1 = f"{field} - Individual: ₹{int(ind_val):,}" if pd.notnull(ind_val) else f"{field} - Individual: N/A"
            text2 = f"{field} - Corporate: ₹{int(corp_val):,}" if pd.notnull(corp_val) else f"{field} - Corporate: N/A"
            c.drawString(50, y, text1)
            y -= 14
            c.drawString(50, y, text2)
            y -= 18

        c.save()
        return tmp.name

if st.button("📥 Download as PDF"):
    pdf_path = generate_pdf(row)
    with open(pdf_path, "rb") as f:
        st.download_button("Download PDF", f, file_name=f"{model}_{variant}_pricing.pdf", mime="application/pdf")
