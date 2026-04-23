import pandas as pd

def demographic_parity(df, sensitive_col, target_col, positive_value=1):
    groups = df[sensitive_col].dropna().unique()

    if len(groups) < 2:
        return {"error": "Need at least 2 groups"}

    rates = {}

    for group in groups:
        subset = df[df[sensitive_col] == group]
        rate = (subset[target_col] == positive_value).mean()
        rates[str(group)] = round(float(rate), 3)

    vals = list(rates.values())
    diff = round(max(vals) - min(vals), 3)

    risk = "LOW"
    if diff > 0.10:
        risk = "MEDIUM"
    if diff > 0.20:
        risk = "HIGH"

    return {
        "approval_rates": rates,
        "demographic_parity_diff": diff,
        "risk_level": risk
    }