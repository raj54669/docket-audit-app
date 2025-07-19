import streamlit as st
import pandas as pd
import re
import io

# === Normalize helpers ===
def normalize(text):
    if not isinstance(text, str):
        return ""
    text = text.upper().replace("SCOPRIO", "SCORPIO")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def normalize_model(text):
    return normalize(text)

# === Discount rule parser ===
def parse_discount_model(entry: str):
    if not isinstance(entry, str):
        return None

    original = entry.strip()
    cleaned = re.sub(r"\s*[-–—]\s*20\d{2}", "", original)
    parens = re.findall(r"\(([^()]*)\)", cleaned)

    model = re.split(r"\(", cleaned)[0].strip()
    model = normalize_model(model)

    fuel = None
    variants = []
    rule_type = "all"

    fuel_candidates = {"PETROL", "DIESEL", "EV"}
    for p in parens:
        tokens = [normalize(t) for t in re.split(r"[,&]", p)]
        for t in tokens:
            if t in fuel_candidates:
                fuel = t.capitalize()
                break

    # Fuel fallback from full string
    if not fuel:
        if "DIESEL" in original.upper():
            fuel = "Diesel"
        elif "PETROL" in original.upper():
            fuel = "Petrol"
        elif "EV" in original.upper():
            fuel = "EV"

    text_upper = original.upper()

    if "ALL EXCEPT" in text_upper:
        rule_type = "all_except"
        match = re.search(r"ALL EXCEPT ([^)]+)\)?", text_upper)
        if match:
            variants = [normalize(v) for v in re.split(r"[&,]", match.group(1)) if v.strip()]
    elif any(w in text_upper for w in ["SERIES", "Z8", "AX7 SERIES"]):
        rule_type = "prefix_include"
        for p in parens:
            variants += [normalize(v) for v in re.split(r"[&,]", p) if "SERIES" in p or "Z8" in p]
    elif "MOCHA" in text_upper:
        rule_type = "all_except"
        variants = ["MOCHA INTERIORS"]
    elif "TGDI" in text_upper and "AX5" in text_upper:
        rule_type = "include_all"
        variants = ["AX5", "TGDI"]
    elif "BLACK EDITION" in text_upper:
        rule_type = "exact_model_all"
    elif "BE 6" in text_upper or "XEV 9E" in text_upper:
        rule_type = "exact_model_all"
    elif parens:
        rule_type = "include_any"
        for p in parens:
            variants += [normalize(v) for v in re.split(r"[&,]", p)]

    return {
        "original": original,
        "model": model,
        "fuel": fuel,
        "rule_type": rule_type,
        "variants": variants
    }

# === Load and clean audit data ===
def load_and_clean_audit(file):
    df = pd.read_excel(file)
    df = df[["Model", "Fuel Type", "Variant"]].dropna()
    df["Model"] = df["Model"].apply(normalize_model)
    df["Fuel Type"] = df["Fuel Type"].apply(normalize)
    df["Variant"] = df["Variant"].apply(normalize)
    return df

# === Rule engine for matching ===
def is_match(row, parsed):
    model = normalize_model(row["Model"])
    fuel = normalize(row["Fuel Type"])
    variant = normalize(row["Variant"])

    p_model = parsed["model"]
    p_fuel = parsed["fuel"]
    rule = parsed["rule_type"]
    terms = parsed["variants"]

    # Model match (allow loose match)
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

    # Fuel match
    if p_fuel and p_fuel.upper() != fuel:
        return False

    # Rule logic
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
                    audit_df.at[idx, "Match Reason"] = f"Matched by rule: {parsed['rule_type']}"

    return audit_df

# === Streamlit UI ===
st.set_page_config(page_title="Discount Matcher", layout="wide")
st.title("🧾 Discount Adherence Matcher (Top 13 Rows)")

with st.sidebar:
    st.header("📂 Upload Files")
    discount_file = st.file_uploader("Discount Sheet (Excel)", type=["xlsx"])
    audit_file = st.file_uploader("Audit Sheet (Excel)", type=["xlsx"])

if discount_file and audit_file:
    st.success("✅ Files uploaded successfully.")

    if st.button("🔍 Run Matching Logic"):
        with st.spinner("Matching in progress..."):
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
    st.info("📄 Please upload both Discount and Audit Excel files to start.")
