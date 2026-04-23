import pandas as pd
from .sensitive_detector import detect_sensitive_columns

def profile_dataframe(df: pd.DataFrame):
    return {
        "rows": len(df),
        "columns": list(df.columns),
        "num_columns": len(df.columns),
        "missing_values": int(df.isnull().sum().sum()),
        "sensitive_columns": detect_sensitive_columns(df.columns)
    }