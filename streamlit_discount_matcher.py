import streamlit as st
import pandas as pd
import re
import io

# === Normalize helper ===
def normalize(text):
    if not isinstance(text, str):
        return ""
    text = text.upper().replace("-", " ").replace("SCOPRIO", "SCORPIO")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# === Parse discount row ===
def parse_discount_model(entry: str):
    """
    Handles entries like:
    - "XUV 3XO (Petrol) - 2025 (All Except AX7 Series & AX5 PM AT)"
    - "XUV 700 (AX3 & AX5)"
    - "XUV 3XO (Diesel)"
    """
    if not isinstance(entry, str):
        return None

    original = entry.strip()
    cleaned = re.sub(r"\s*[-–—]\s*20\d{2}", "", original)  # Remove year suffix like '- 2025'
    parens = re.findall(r"\(([^()]*)\)", cleaned)

    model = re.split(r"\(", cleaned)[0].strip()
    model = normalize(model)

    fuel = None
    variants = []
    variant_mode = "all"

    # Step 1: Fuel detection
    fuel_candidates = {"PETROL", "DIESEL", "EV"}
    for p in parens:
        tokens = [normalize(t) for t in re.split(r"[,&]", p)]
        for t in tokens:
            if t in fuel_candidates:
                fuel = t.capitalize()
                break

    # Step 2: All Except
    for p in parens:
        if "all except" in p.lower():
            variant_mode = "all_except"
            variant_str = re.sub(r"(?i)all except", "", p)
            variants = [normalize(v) for v in re.split(r"[&,]", variant_str) if v.strip()]
            break
    else:
        # Step 3: Included variants (with fuel safety check)
        for p in parens:
            if any(c.isalnum() for c in p) and (not fuel or fuel.lower() not in p.lower()):
                variants = [normalize(v) for v in re.split(r"[&,]", p) if v.strip()]
                if variants:
                    variant_mode = "include"
                    break

    return {
        "original": original,
        "model": model,
        "fuel": fuel,
        "variant_mode": variant_mode,
        "variants": variants
    }

# === Load and clean audit data ===
def load_and_clean_audit(file):
    df = pd.read_excel(file)
    df = df[["Model", "Fuel Type", "Variant"]].dropna()
    df["Model"] = df["Model"].apply(normalize)
    df["Fuel Type"] = df["Fuel Type"].apply(normalize)
    df["Variant"] = df["Variant"].apply(normalize)
    return df

# === Flexible matching ===
def is_match(row, parsed):
    model = row["Model"]
    fuel = row["Fuel Type"]
    variant = row["Variant"]

    # Model match
    if parsed["model"] not in model and model not in parsed["model"]:
        return False

    # Fuel match
    if parsed["fuel"] and parsed["fuel"].upper() != fuel:
        return False

    # Special case: THAR ROXX except MOCHA
    if "THAR ROXX" in parsed["model"]:
        if "THAR ROXX" not in model:
            return False
        if "MOCHA INTERIORS" in variant:
            return False

    # Ignore BE 6 or XEV 9E models
    if "BE 6" in parsed["model"] or "XEV 9E" in parsed["model"]:
        return False

    # Variant logic
    if parsed["variant_mode"] == "include" and parsed["variants"]:
        return any(v in variant or variant.startswith(v) for v in parsed["variants"])
    elif parsed["variant_mode"] == "all_except" and parsed["variants"]:
        return all(v not in variant and not variant.startswith(v) for v in parsed["variants"])

    return True

# === Process all matches ===
def generate_matched_audit(discount_file, audit_file):
    audit_df = load_and_clean_audit(audit_file)

    # Load first 14 rows and skip the first (title) row
    discount_df = pd.read_excel(discount_file, sheet_name=0).head(14).iloc[1:]

    audit_df["Matched Discount Entry"] = "Not Matched"

    for _, row in discount_df.iterrows():
        parsed = parse_discount_model(row["Model"])
        if not parsed:
            continue

        for idx in audit_df.index:
            if audit_df.at[idx, "Matched Discount Entry"] == "Not Matched":
                if is_match(audit_df.loc[idx], parsed):
                    audit_df.at[idx, "Matched Discount Entry"] = parsed["original"]

    return audit_df

# === Streamlit UI ===
st.set_page_config(page_title="Discount Matcher (Improved)", layout="wide")
st.title("🧾 Discount Adherence Matcher (Improved Parsing, Top 13 Entries)")

with st.sidebar:
    st.header("📂 Upload Required Files")
    discount_file = st.file_uploader("Discount Sheet (Excel)", type=["xlsx"])
    audit_file = st.file_uploader("Audit Sheet (Excel)", type=["xlsx"])

if discount_file and audit_file:
    st.success("✅ Files uploaded! Click below to start matching.")

    if st.button("🔍 Run Matching Logic"):
        with st.spinner("Processing files..."):
            matched_df = generate_matched_audit(discount_file, audit_file)

        st.subheader("🔗 Matched Results Preview")
        st.dataframe(matched_df.head(50), use_container_width=True)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            matched_df.to_excel(writer, index=False)

        st.download_button(
            label="📥 Download Full Matched File",
            data=output.getvalue(),
            file_name="matched_audit_discount.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("📄 Upload both Discount and Audit Excel files to begin.")
