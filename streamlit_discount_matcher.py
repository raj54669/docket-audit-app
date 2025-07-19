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

def normalize_model(text):
    return normalize(text.replace("-", " ").replace("(", "").replace(")", ""))

# === Extract fuel ===
def extract_fuel_from_anywhere(text):
    text = normalize(text)
    if "DIESEL" in text:
        return "Diesel"
    if "PETROL" in text:
        return "Petrol"
    if "EV" in text:
        return "Ev"
    return None

# === Discount parsing using REMARK logic ===
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
    rule_type = "all"

    if any(x in model for x in ["BLACK EDITION", "BE 6", "XEV 9E"]):
        rule_type = "exact_model_all"
    elif "all except" in entry.lower():
        rule_type = "all_except"
        variant_str = re.sub(r"(?i)all except", "", parens[-1] if parens else "")
        variants = [normalize(v) for v in re.split(r"[&,]", variant_str) if v.strip()]
    elif parens:
        for p in parens:
            if any(c.isalnum() for c in p) and (not fuel or fuel.lower() not in p.lower()):
                terms = [normalize(v) for v in re.split(r"[&,]", p) if v.strip()]
                if terms:
                    variants = terms
                    rule_type = "include_all"
                    break

    return {
        "original": original,
        "model": model,
        "fuel": fuel,
        "variants": variants,
        "rule_type": rule_type
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

    # Model match
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
