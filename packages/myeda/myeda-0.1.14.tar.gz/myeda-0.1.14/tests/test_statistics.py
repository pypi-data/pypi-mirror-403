import pandas as pd
from myeda import numeric_summary, categorical_summary


def test_numeric_summary_basic():
    df = pd.DataFrame({"A": [1, 2, 3], "B": [4.0, 5.0, 6.0]})
    result = numeric_summary(df)
    assert not result.empty
    assert "skewness" in result.columns


def test_categorical_summary_basic():
    df = pd.DataFrame({"A": ["x", "y", "x"]})
    result = categorical_summary(df)
    assert not result.empty
    assert "unique_values" in result.columns
