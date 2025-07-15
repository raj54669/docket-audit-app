import pandas as pd
import streamlit as st

@st.cache_data
def load_price_data():
    return pd.read_excel("PV Price List Master D. 08.07.2025.xlsx")

def get_filtered_row(df, model, fuel_type, variant):
    return df[
        (df["Model"] == model) &
        (df["Fuel Type"] == fuel_type) &
        (df["Variant"] == variant)
    ]

def format_currency(value):
    return f"₹{int(value):,}" if pd.notnull(value) else "Not Available"
