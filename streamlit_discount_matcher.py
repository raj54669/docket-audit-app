import streamlit as st
import pandas as pd
import re
import io

# === Normalize helpers ===
def normalize(text):
    if not isinstance(text, str):
        return ""
    return re.sub(r"\s+", " ", text.upper().replace("-", " ").replace("SCOPRIO", "SCORPIO")).strip()

def normalize_model(text):
    return normalize(text)

def extract_fuel_from_anywhere(text):
    text = normalize(text)
    if "DIESEL" in text:
        return "Diesel"
    if "PETROL" in text:
        return "Petrol"
    if "EV" in text:
        return "Ev"
    return None

# === Parse discount row ===
def parse_discount_model(entry):
    if not isinstance(entry, str):
        return None

    original = entry.strip()
    cleaned = re.sub(r"\s*[-–—]\s*20\d{2}", "", original)
    parens = re.findall(r"\(([^()]*)\)", cleaned)
    model = re.split(r"\(", cleaned)[0].strip()
    model = normalize(model)

    fuel = extract_fuel_from_anywhere(entry)
    variants = []
    variant_mode = "all"

    for p in parens:
        if "all except" in p.lower():
            variant_mode = "all_except"
            variant_str = re.sub(r"(?i)all except", "", p)
            variants = [normalize(v) for v in re.split(r"[&,]", variant_str) if v.strip()]
            break
        elif any(c.isalnum() for c in p) and (not fuel or fuel.lower() not in p.lower()):
            variants = [normalize(v) for v in re.split(r"[&,]", p) if v.strip()]
            if variants:
                variant_mode = "include"
                break

    return {
        "original": original,
        "model": model,
        "fuel": fuel,
        "variant_mode": variant_mode,
        "variants": variants,
        "rule_type": "all" if not variants else (
            "all_except" if variant_mode == "all_except" else "include_all"
        )
    }

# === Rule engine for matching ===
def is_match(row, parsed):
    model = normalize_model(row["Model"])
    fuel = normalize(row["Fuel Type"])
    variant = normalize(row["Variant"])

    p_model = parsed["model"]
    p_fuel = parsed["fuel"]
    rule = parsed["rule_type"]
    terms = parsed["variants"]

    if rule == "exact_model_all":
        if p_model != model:
            return False
    else:
        if not (
            p_model in model or
            model in p_model or
            model.endswith(p_model) or
            p_model.endswith(model)
        ):
            return False

    if p_fuel and p_fuel.upper() != fuel:
        return False

    if rule == "all":
        return True
    elif rule == "include_any":
        return any(term in variant for term in terms)
    elif rule == "include_all":
        return all(term in variant for term in terms)
    elif rule == "prefix_include":
        return any(variant.startswith(term) for term in terms)
    elif rule == "all_except":
        return all(term not in variant for term in terms)

    return False

# === Load and clean audit data ===
def load_and_clean_audit(file):
    df = pd.read_excel(file)
    df = df[["Model", "Fuel Type", "Variant"]].dropna()
    df["Model"] = df["Model"].apply(normalize)
    df["Fuel Type"] = df["Fuel Type"].apply(normalize)
    df["Variant"] = df["Variant"].apply(normalize)
    return df

# === Process all matches ===
def generate_matched_audit(discount_file, audit_file):
    audit_df = load_and_clean_audit(audit_file)
    discount_df = pd.read_excel(discount_file, sheet_name=0).head(14).iloc[1:]

    audit_df["Matched Discount Entry"] = "Not Matched"
    audit_df["Match Reason"] = ""

    for _, row in discount_df.iterrows():
        parsed = parse_discount_model(row["Model"])
        if not parsed:
            continue

        for idx in audit_df.index:
            if audit_df.at[idx, "Matched Discount Entry"] == "Not Matched":
                if is_match(audit_df.loc[idx], parsed):
                    audit_df.at[idx, "Matched Discount Entry"] = parsed["original"]
                    audit_df.at[idx, "Match Reason"] = f"Matched Rule: {parsed['rule_type']}"

    return audit_df

# === Streamlit UI ===
st.set_page_config(page_title="Discount Matcher", layout="wide")
st.title("🧾 Discount Adherence Matcher")

with st.sidebar:
    st.header("📂 Upload Files")
    discount_file = st.file_uploader("Discount Sheet (Excel)", type=["xlsx"])
    audit_file = st.file_uploader("Audit Sheet (Excel)", type=["xlsx"])

if discount_file and audit_file:
    st.success("✅ Files uploaded! Click below to start matching.")

    if st.button("🔍 Run Matching Logic"):
        with st.spinner("Processing..."):
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
