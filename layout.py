import streamlit as st
from utils import format_currency

def render_pricing_details(row):
    fields = [
        "Ex-Showroom Price", "TCS 1%", "Insurance 1 Yr OD + 3 Yr TP + Zero Dep.",
        "Accessories Kit", "SMC", "Extended Warranty", "Maxi Care"
    ]
    pricing_html = "<ul>"
    for field in fields:
        value = row.iloc[0].get(field, None)
        pricing_html += f"<li><strong>{field}</strong>: {format_currency(value)}</li>"
    pricing_html += "</ul>"
    st.markdown(pricing_html, unsafe_allow_html=True)

def render_rto_table(row):
    st.markdown("""
        <style>
        .rto-layout {
            width: 100%;
            border-collapse: collapse;
        }
        .rto-layout th, .rto-layout td {
            border: 1px solid #999;
            padding: 8px;
            text-align: center;
        }
        .rto-layout th {
            background-color: #004d40;
            color: white;
        }
        .rto-layout td:first-child {
            font-weight: bold;
            background-color: #e0f2f1;
        }
        </style>
    """, unsafe_allow_html=True)

    table_html = """
    <table class='rto-layout'>
        <tr><th>Category</th><th>RTO (W/O HYPO)</th><th>RTO (With HYPO)</th></tr>
    """
    for category in ["Individual", "Corporate"]:
        rto_wo = row.iloc[0].get(f"RTO (W/O HYPO) - {category}", None)
        rto_with = row.iloc[0].get(f"RTO (With HYPO) - {category}", None)
        table_html += f"<tr><td>{category}</td><td>{format_currency(rto_wo)}</td><td>{format_currency(rto_with)}</td></tr>"
    table_html += "</table>"
    st.markdown(table_html, unsafe_allow_html=True)
