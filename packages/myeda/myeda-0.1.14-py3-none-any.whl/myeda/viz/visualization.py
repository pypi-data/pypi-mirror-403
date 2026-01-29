from __future__ import annotations
import pandas as pd 
import matplotlib.pyplot as plt 


def plot_numeric_distribution(
    df: pd.DataFrame,
    column: str,
    bins: int = 30
) -> None:
  """
  Plots a histogram for a numeric column.
  """

  if not isinstance(df, pd.DataFrame):
    raise TypeError("Input must be a pandas DataFrame")
  
  if column not in df.columns:
    raise KeyError(f"column {column} not found in DataFrame")
  
  if not pd.api.types.is_numeric_dtype(df[column]):
    raise TypeError(f"column {column} must be numeric")
  
  df[column].dropna().hist(bins=bins)
  plt.title(f"Distribution of {column}")
  plt.xlabel(column)
  plt.ylabel("frequency")
  plt.tight_layout()
  plt.show()


def plot_boxplot(
    df: pd.DataFrame,
    column: str,
) -> None:
  """
  Plots a boxplot for a numeric column.
  """
  if not isinstance(df, pd.DataFrame):
      raise TypeError("Input must be a pandas DataFrame")

  if column not in df.columns:
      raise KeyError(f"Column '{column}' not found in DataFrame")

  if not pd.api.types.is_numeric_dtype(df[column]):
      raise TypeError(f"Column '{column}' must be numeric")

  plt.boxplot(df[column].dropna())
  plt.title(f"boxplot of {column}")
  plt.tight_layout()
  plt.show()


def plot_categorical_counts(
      df: pd.DataFrame,
      column: str,
      top_n: int | None = None 
) -> None:
  """
  Plots a bar chart of value counts for a categorical column.
  """
  if not isinstance(df, pd.DataFrame):
      raise TypeError("Input must be a pandas DataFrame")

  if column not in df.columns:
      raise KeyError(f"Column '{column}' not found in DataFrame")

  counts = df[column].value_counts(dropna=True)

  if counts.empty:
     print("No values to plot")
     return
  
  if top_n is not None:
     counts = counts.head(top_n)

  counts.plot(kind="bar")
  plt.title(f"counts of {column}")
  plt.xlabel(column)
  plt.ylabel("count")
  plt.tight_layout()
  plt.show()



def plot_correlation_heatmap(
      df: pd.DataFrame,
      method: str = "pearson"
) -> None:
  """
  Plots a correlation heatmap for numeric columns.
  """
  if not isinstance(df, pd.DataFrame):
      raise TypeError("Input must be a pandas DataFrame")

  num_df = df.select_dtypes(include="number")

  if num_df.shape[1] < 2:
    print("Not enough numeric columns for correlation")
    return
  corr = num_df.corr(method=method)

  plt.imshow(corr, aspect="auto")
  plt.colorbar()
  plt.xticks(range(len(corr.columns)), corr.columns, rotation = 90)
  plt.yticks(range(len(corr.columns)),corr.columns)
  plt.title("Correlation Heatmap")
  plt.tight_layout()
  plt.show()