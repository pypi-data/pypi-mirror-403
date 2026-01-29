import pandas as pd


def dataset_overview(df: pd.DataFrame) -> dict:
    """
    Returns a high-level overview of the dataset.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")

    total_rows, total_columns = df.shape

    overview = {
        "rows": total_rows,
        "columns": total_columns,
        "numeric_columns": len(df.select_dtypes(include="number").columns),
        "categorical_columns": len(
            df.select_dtypes(include=["object", "category", "string"]).columns
        ),
        "boolean_columns": len(df.select_dtypes(include="bool").columns),
        "datetime_columns": len(df.select_dtypes(include="datetime").columns),
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_percentage": (
            (df.duplicated().sum() / total_rows) * 100 if total_rows > 0 else 0
        ),
        "memory_usage_mb": round(
            df.memory_usage(deep=True).sum() / (1024 * 1024), 2
        ),
    }

    return overview
