from __future__ import annotations
import pandas as pd

from myeda.core.overview import dataset_overview
from myeda.core.missing import missing_overview, missing_summary
from myeda.core.statistics import numeric_summary, categorical_summary
from myeda.viz.visualization import (
    plot_numeric_distribution,
    plot_boxplot,
    plot_categorical_counts,
    plot_correlation_heatmap,
)


class EDAReport:
    """
    Lightweight orchestrator for Exploratory Data Analysis.
    """

    def __init__(self, df: pd.DataFrame):
        if not isinstance(df, pd.DataFrame):
            raise TypeError("EDAReport expects a pandas DataFrame")
        self.df = df

    def overview(self) -> dict:
        """
        Returns dataset-level overview.
        """
        return dataset_overview(self.df)

    def missing(self) -> dict:
        """
        Returns missing value overview and summary.
        """
        return {
            "overview": missing_overview(self.df),
            "summary": missing_summary(self.df),
        }

    def statistics(self) -> dict:
        """
        Returns numeric and categorical summaries.
        """
        return {
            "numeric": numeric_summary(self.df),
            "categorical": categorical_summary(self.df),
        }

    def visualize(
        self,
        numeric_column: str | None = None,
        categorical_column: str | None = None,
        correlation: bool = False,
    ) -> None:
        """
        Optional visualizations.
        """
        if numeric_column is not None:
            plot_numeric_distribution(self.df, numeric_column)
            plot_boxplot(self.df, numeric_column)

        if categorical_column is not None:
            plot_categorical_counts(self.df, categorical_column)

        if correlation:
            plot_correlation_heatmap(self.df)

    def run(self) -> dict:
        """
        Runs a complete lightweight EDA (no plots).
        """
        return {
            "overview": self.overview(),
            "missing": self.missing(),
            "statistics": self.statistics(),
        }
