import pandas as pd
import matplotlib.pyplot as plt 


def missing_summary(df: pd.DataFrame) -> pd.DataFrame:
  """
  Returns a summary of missing values per column.

  Output columns:
  - missing_count
  - missing_percent

   Only columns with missing values are included.
  """
  if not isinstance(df, pd.DataFrame):
    raise TypeError("Input must be a pandas DataFrame")
  
  total_rows = len(df)

  missing_count = df.isnull().sum()
  missing_percent = (missing_count/total_rows)*100

  summary = pd.DataFrame({
    "missing_count" : missing_count,
    "missing_percent" : missing_percent
  })

  summary = summary[summary['missing_count']>0]
  summary = summary.sort_values(by='missing_percent',ascending=False)

  return summary            


def missing_overview(df: pd.DataFrame) -> dict:
  """
  Returns dataset-level missing value overview.
  """
  if not isinstance(df, pd.DataFrame):
    raise TypeError("Input must be a pandas DataFrame")
  
  total_cell = df.shape[0] * df.shape[1]
  total_missing = df.isnull().sum().sum()

  return {
    "total_rows" : df.shape[0],
    "total_columns" : df.shape[1],
    "total_missing_values" : int(total_missing),
    "missing_percentage" : (total_missing / total_cell)*100,
    "column_with_missing" : int((df.isnull().sum()>0).sum())
  }

def rows_with_missing(df: pd.DataFrame) -> pd.DataFrame:
  """
  Returns rows that contain at least one missing value.
  """

  if not isinstance(df, pd.DataFrame):
    raise TypeError("Input must be a pandas DataFrame")
  
  return df[df.isnull().any(axis=1)]

def plot_missing(df: pd.DataFrame) -> None:
  """
  Plots a simple bar chart of missing value percentage per column.
  """

  summary = missing_summary(df)

  if summary.empty:
    print("No missing values found.")
    return
  
  summary['missing_percent'].plot(
    kind="bar",
    title="Missing values percentage per column"
  )
  plt.ylabel("Missing percentage")
  plt.xlabel("Columns")
  plt.tight_layout()
  plt.show()