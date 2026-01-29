from __future__ import annotations
import pandas as pd


def numeric_summary(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")

    num_df = df.select_dtypes(include="number")

    if num_df.empty:
        return pd.DataFrame()

    summary = num_df.describe().T
    summary["skewness"] = num_df.skew()
    summary["kurtosis"] = num_df.kurtosis()

    return summary


def categorical_summary(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")

    cat_df = df.select_dtypes(include=["object", "category"])

    if cat_df.empty:
        return pd.DataFrame()

    rows = []

    for col in cat_df.columns:
        value_counts = cat_df[col].value_counts(dropna=True)

        rows.append({
            "column": col,
            "unique_values": cat_df[col].nunique(dropna=True),
            "most_frequent": value_counts.index[0] if not value_counts.empty else None,
            "frequency": int(value_counts.iloc[0]) if not value_counts.empty else 0
        })

    result = pd.DataFrame.from_records(rows)

    if "column" not in result.columns:
        raise RuntimeError(
            f"Internal error: expected 'column' in result, got {list(result.columns)}"
        )

    return result.set_index("column")
