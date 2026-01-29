# myeda

[![PyPI version](https://img.shields.io/pypi/v/myeda)](https://pypi.org/project/myeda/)
[![Total Downloads](https://static.pepy.tech/personalized-badge/myeda?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=BLUE&left_text=downloads)](https://pepy.tech/projects/myeda)
[![Monthly Downloads](https://static.pepy.tech/personalized-badge/myeda?period=monthly&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=GREEN&left_text=monthly)](https://pepy.tech/projects/myeda)
[![GitHub stars](https://img.shields.io/github/stars/KHAJA-MUBASHIR-ARSALAN/myeda?style=social)](https://github.com/KHAJA-MUBASHIR-ARSALAN/myeda)
[![License](https://img.shields.io/github/license/KHAJA-MUBASHIR-ARSALAN/myeda)](https://github.com/KHAJA-MUBASHIR-ARSALAN/myeda/blob/main/LICENSE)
[![CI Status](https://github.com/KHAJA-MUBASHIR-ARSALAN/myeda/actions/workflows/ci.yml/badge.svg)](https://github.com/KHAJA-MUBASHIR-ARSALAN/myeda/actions/workflows/ci.yml)
[![Python Versions](https://img.shields.io/pypi/pyversions/myeda)](https://pypi.org/project/myeda/)



A lightweight Exploratory Data Analysis (EDA) library that provides one-line statistical summaries and optional visualizations for faster data understanding.

# Features

One-line EDA summaries

Missing value analysis

Descriptive statistics

Optional visualizations (explicit, not automatic)

Clean, modular API

Beginner-friendly and extensible

# Installation

```
pip install myeda
```


# Basic Usage
```
import pandas as pd
from myeda import overview, report

df = pd.read_csv("titanic_dataset.csv")

overview(df)
report(df)
```

# Visualizations

```
from myeda.viz import (
    plot_numeric_distribution,
    plot_boxplot,
    plot_categorical_counts,
    plot_correlation_heatmap
)

plot_numeric_distribution(df, "Age")
plot_boxplot(df, "Fare")
plot_categorical_counts(df, "Sex")
plot_correlation_heatmap(df)
```

Visualizations are never automatic — you control when to plot.

## Project Structure

```
EDA/
|-- examples/
|   |-- titanic_dataset.csv
|   `-- titanic_demo.ipynb
|
|-- myeda/
|   |-- __init__.py
|   |-- report.py
|   |
|   |-- core/
|   |   |-- overview.py
|   |   |-- missing.py
|   |   `-- statistics.py
|   |
|   `-- viz/
|       `-- visualization.py
|
|-- tests/
|   `-- test_statistics.py
|
|-- setup.py
|-- pyproject.toml
|-- requirements.txt
|-- README.md
|-- LICENSE
`-- .gitignore

```



# Module Responsibilities
### core/overview.py

Dataset shape

Column types

Basic dataset information

### core/missing.py

Missing value counts

Missing percentage per column

### core/statistics.py

Mean, median, mode

Variance, standard deviation

Numerical summaries

### viz/visualization.py

Numeric distributions

Boxplots

Categorical counts

Correlation heatmaps

# Examples

Check the examples/ directory for:

Titanic dataset

Jupyter notebook demonstrating full EDA workflow


# How users can import EVERYTHING


### Dataset overview
```
from myeda import dataset_overview

dataset_overview(df)
```

### Missing-value analysis

```
from myeda import missing_overview, missing_summary

missing_overview(df)
missing_summary(df)
```

### Statistical summaries

```
from myeda import numeric_summary, categorical_summary

numeric_summary(df)
categorical_summary(df)
```

### Visualizations (explicit & optional)

```
from myeda import (
    plot_numeric_distribution,
    plot_boxplot,
    plot_categorical_counts,
    plot_correlation_heatmap,
)

plot_numeric_distribution(df, "Age")
plot_boxplot(df, "Fare")
plot_categorical_counts(df, "Sex")
plot_correlation_heatmap(df)
```

### Full EDA (recommended)

```
from myeda import EDAReport

eda = EDAReport(df)
results = eda.run()
```

# Testing
pytest

# License

MIT License

# Author

Khaja Mubashir Arsalan
