import pandas as pd
import plotly.express as px


def get_numeric_columns(df: pd.DataFrame, column_summary_df: pd.DataFrame) -> list:
    numeric_columns = column_summary_df[
        column_summary_df["Detected Type"] == "Numeric"
    ]["Column"].tolist()

    useful_numeric_columns = []

    for column in numeric_columns:
        if df[column].dropna().nunique() > 1:
            useful_numeric_columns.append(column)

    return useful_numeric_columns


def get_categorical_columns(df: pd.DataFrame, column_summary_df: pd.DataFrame) -> list:
    categorical_columns = column_summary_df[
        column_summary_df["Detected Type"] == "Categorical"
    ]["Column"].tolist()

    useful_categorical_columns = []

    for column in categorical_columns:
        unique_count = df[column].dropna().nunique()

        if unique_count >= 1:
            useful_categorical_columns.append(column)

    return useful_categorical_columns


def get_date_columns(column_summary_df: pd.DataFrame) -> list:
    return column_summary_df[
        column_summary_df["Detected Type"] == "Date/time"
    ]["Column"].tolist()


def generate_numeric_summary(df: pd.DataFrame, column: str) -> dict:
    numeric_series = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    non_missing_series = numeric_series.dropna()

    if non_missing_series.empty:
        return {
            "missing_count": int(numeric_series.isna().sum()),
            "non_missing_count": 0,
            "mean": 0,
            "median": 0,
            "standard_deviation": 0,
            "minimum": 0,
            "maximum": 0
        }

    return {
        "missing_count": int(numeric_series.isna().sum()),
        "non_missing_count": int(non_missing_series.count()),
        "mean": float(non_missing_series.mean()),
        "median": float(non_missing_series.median()),
        "standard_deviation": float(non_missing_series.std()),
        "minimum": float(non_missing_series.min()),
        "maximum": float(non_missing_series.max())
    }


def generate_numeric_histogram(df: pd.DataFrame, column: str):
    chart_df = df[[column]].copy()
    chart_df[column] = pd.to_numeric(
        chart_df[column],
        errors="coerce"
    )
    chart_df = chart_df.dropna(subset=[column])

    fig = px.histogram(
        chart_df,
        x=column,
        title=f"Distribution of {column}",
        nbins=30
    )

    fig.update_layout(
        xaxis_title=column,
        yaxis_title="Number of rows"
    )

    return fig


def generate_categorical_summary(df: pd.DataFrame, column: str) -> dict:
    non_missing_series = df[column].dropna().astype(str)

    if non_missing_series.empty:
        return {
            "missing_count": int(df[column].isna().sum()),
            "non_missing_count": 0,
            "most_common_category": None,
            "most_common_count": 0,
            "most_common_percentage": 0
        }

    value_counts = non_missing_series.value_counts()
    most_common_category = value_counts.index[0]
    most_common_count = int(value_counts.iloc[0])
    non_missing_count = int(non_missing_series.count())
    most_common_percentage = (most_common_count / non_missing_count) * 100

    return {
        "missing_count": int(df[column].isna().sum()),
        "non_missing_count": non_missing_count,
        "most_common_category": most_common_category,
        "most_common_count": most_common_count,
        "most_common_percentage": most_common_percentage
    }


def generate_categorical_bar_chart(df: pd.DataFrame, column: str):
    chart_df = (
        df[column]
        .dropna()
        .astype(str)
        .value_counts()
        .head(10)
        .reset_index()
    )

    chart_df.columns = [column, "Count"]

    fig = px.bar(
        chart_df,
        x="Count",
        y=column,
        orientation="h",
        title=f"Top 10 categories in {column}"
    )

    fig.update_layout(
        xaxis_title="Number of rows",
        yaxis_title=column,
        yaxis={
            "categoryorder": "total ascending"
        }
    )

    return fig


def generate_date_trend_chart(df: pd.DataFrame, column: str):
    chart_df = df[[column]].copy()
    chart_df[column] = pd.to_datetime(
        chart_df[column],
        errors="coerce"
    )

    missing_count = int(chart_df[column].isna().sum())
    chart_df = chart_df.dropna(subset=[column])

    date_summary = {
        "missing_count": missing_count,
        "non_missing_count": int(len(chart_df))
    }

    if chart_df.empty:
        return None, date_summary

    chart_df["Date Period"] = chart_df[column].dt.to_period("M").dt.to_timestamp()

    trend_df = (
        chart_df
        .groupby("Date Period")
        .size()
        .reset_index(name="Row Count")
    )

    if trend_df.empty:
        return None, date_summary

    fig = px.line(
        trend_df,
        x="Date Period",
        y="Row Count",
        markers=True,
        title=f"Number of records over time using {column}"
    )

    fig.update_layout(
        xaxis_title=column,
        yaxis_title="Number of rows"
    )

    return fig, date_summary


def generate_correlation_heatmap(df: pd.DataFrame, numeric_columns: list):
    usable_numeric_columns = []

    for column in numeric_columns:
        numeric_series = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        if numeric_series.dropna().nunique() > 1:
            usable_numeric_columns.append(column)

    if len(usable_numeric_columns) < 2:
        return None

    correlation_df = df[usable_numeric_columns].corr(numeric_only=True)

    fig = px.imshow(
        correlation_df,
        text_auto=".2f",
        title="Correlation heatmap",
        color_continuous_scale="RdBu",
        zmin=-1,
        zmax=1
    )

    fig.update_layout(
        xaxis_title="Numeric columns",
        yaxis_title="Numeric columns"
    )

    return fig