SENSITIVE_KEYWORDS = [
    "gender", "sex", "race", "ethnicity",
    "age", "religion", "marital", "nationality"
]

def detect_sensitive_columns(columns):
    found = []

    for col in columns:
        lower = col.lower()
        for keyword in SENSITIVE_KEYWORDS:
            if keyword in lower:
                found.append(col)
                break

    return found