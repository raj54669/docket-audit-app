import streamlit as st
import pandas as pd
import re
import io

# === Parse discount sheet row ===
def parse_discount_model(raw_model):
    if not isinstance(raw_model, str):
        return None

    original = raw_model.strip()
    cleaned = re.sub(r'20\d{2}', '', original)
    cleaned = cleaned.replace("-", "").strip()

    fuel_match = re.search(r'\((Petrol|Diesel|EV)\)', cleaned, re.IGNORECASE)
    fuel = fuel_match.group(1).capitalize() if fuel_match else None
    if fuel:
        cleaned = cleaned.replace(fuel_match.group(0), '').strip()

    all_except_match = re.search(r'All Except (.*)\)', original, re.IGNORECASE)
    if all_except_match:
        variant_str = all_except_match.group(1)
        exclusions = [v.strip().upper() for v in re.split(r'[&,]', variant_str)]
        model_type = 'all_except'
        variants = exclusions
        model = re.split(r'\(|-', cleaned)[0].strip().upper()
    else:
        variant_match = re.search(r'\(([^)]+)\)', cleaned)
        if variant_match:
            variant_str = variant_match.group(1)
            variants = [v.strip().upper() for v in re.split(r'[&,]', variant_str)]
            model_type = 'include'
            model = cleaned.replace(variant_match.group(0), '').strip().upper()
        else:
            model_type = 'all'
            variants = []
            model = cleaned.strip().upper()

    return {
        'original': original,
        'model': model,
        'fuel': fuel,
        'variant_mode': model_type,
        'variants': variants
    }

# === Load and normalize audit data ===
def load_and_clean_audit(file):
    df = pd.read_excel(file)
    df.columns = df.columns.str.strip()
    df = df[['Model', 'Fuel Type', 'Variant']].dropna()
    df['Model'] = df['Model'].astype(str).str.upper().str.strip()
    df['Fuel Type'] = df['Fuel Type'].astype(str).str.upper().str.strip()
    df['Variant'] = df['Variant'].astype(str).str.upper().str.strip()
    return df

# === Determine if audit row matches discount rule ===
def is_match(audit_row, parsed):
    model, fuel, variant = audit_row['Model'], audit_row['Fuel Type'], audit_row['Variant']
    if "BLACK EDITION" in parsed['original'].upper():
        if model != parsed['model']:
            return False
    elif "THAR ROXX" in parsed['model']:
        if "THAR ROXX" not in model:
            return False
        if "MOCHA INTERIORS" in variant:
            return False
    elif "BE 6" in parsed['model'] or "XEV 9E" in parsed['model']:
        return False
    else:
        if parsed['model'] not in model:
            return False

    if parsed['fuel'] and parsed['fuel'].upper() != fuel:
        return False

    if parsed['variant_mode'] == 'include' and parsed['variants']:
        return variant in parsed['variants']
    elif parsed['variant_mode'] == 'all_except' and parsed['variants']:
        return variant not in parsed['variants']
    return True

# === Matching Logic ===
def generate_matched_audit(discount_file, audit_file):
    audit_df = load_and_clean_audit(audit_file)
    discount_df = pd.read_excel(discount_file, sheet_name=0)

    audit_df['Matched Discount Entry'] = "Not Matched"

    for _, d_row in discount_df.iterrows():
        parsed = parse_discount_model(d_row['Model'])
        if not parsed:
            continue

        for idx, a_row in audit_df.iterrows():
            if audit_df.at[idx, 'Matched Discount Entry'] == "Not Matched" and is_match(a_row, parsed):
                audit_df.at[idx, 'Matched Discount Entry'] = parsed['original']

    return audit_df

# === Streamlit UI ===
st.set_page_config(page_title="Discount Matcher", layout="wide")
st.title("🧾 Discount Adherence Matcher")

with st.sidebar:
    st.header("Upload Files")
    discount_file = st.file_uploader("Discount File (Excel)", type=["xlsx"])
    audit_file = st.file_uploader("Audit File (Excel)", type=["xlsx"])

if discount_file and audit_file:
    st.success("Files uploaded! Click below to process.")

    if st.button("🔍 Run Matching Logic"):
        matched_df = generate_matched_audit(discount_file, audit_file)
        st.subheader("🔗 Matched Results Preview")
        st.dataframe(matched_df.head(50), use_container_width=True)

        # Prepare download
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            matched_df.to_excel(writer, index=False)
        st.download_button(
            label="📥 Download Matched File",
            data=output.getvalue(),
            file_name="audit_price_list_with_discount_flag.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Upload both Discount and Audit Excel files to begin.")

