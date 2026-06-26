import pandas as pd
import plotly.express as px


def get_useful_numeric_columns(df: pd.DataFrame, column_summary_df: pd.DataFrame) -> list:
    numeric_columns = column_summary_df[
        column_summary_df["Detected Type"] == "Numeric"
    ]["Column"].tolist()

    useful_numeric_columns = []

    for column in numeric_columns:
        if df[column].nunique(dropna=True) > 1:
            useful_numeric_columns.append(column)

    return useful_numeric_columns


def get_useful_categorical_columns(df: pd.DataFrame, column_summary_df: pd.DataFrame) -> list:
    categorical_columns = column_summary_df[
        column_summary_df["Detected Type"] == "Categorical"
    ]["Column"].tolist()

    useful_categorical_columns = []

    for column in categorical_columns:
        unique_count = df[column].nunique(dropna=True)

        if 2 <= unique_count <= 50:
            useful_categorical_columns.append(column)

    return useful_categorical_columns


def generate_automatic_charts(df: pd.DataFrame, column_summary_df: pd.DataFrame) -> list:
    charts = []

    useful_numeric_columns = get_useful_numeric_columns(df, column_summary_df)
    useful_categorical_columns = get_useful_categorical_columns(df, column_summary_df)

    date_columns = column_summary_df[
        column_summary_df["Detected Type"] == "Date/time"
    ]["Column"].tolist()

    # Histograms for up to 2 useful numeric columns
    for column in useful_numeric_columns[:2]:
        fig = px.histogram(
            df,
            x=column,
            title=f"Distribution of {column}",
            nbins=30
        )

        fig.update_layout(
            xaxis_title=column,
            yaxis_title="Number of rows"
        )

        charts.append(
            {
                "subheader": f"Distribution of {column}",
                "figure": fig
            }
        )

    # Bar charts for up to 2 useful categorical columns
    for column in useful_categorical_columns[:2]:
        top_categories = (
            df[column]
            .fillna("Missing")
            .astype(str)
            .value_counts()
            .head(10)
            .reset_index()
        )

        top_categories.columns = [column, "Count"]

        fig = px.bar(
            top_categories,
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

        charts.append(
            {
                "subheader": f"Top categories in {column}",
                "figure": fig
            }
        )

    # Correlation heatmap if there are at least 2 numeric columns
    if len(useful_numeric_columns) >= 2:
        correlation_df = df[useful_numeric_columns].corr(numeric_only=True)

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

        charts.append(
            {
                "subheader": "Correlation Between Numeric Columns",
                "figure": fig
            }
        )

    # Date trend chart if a date column exists
    if date_columns:
        date_column = date_columns[0]

        chart_df = df.copy()
        chart_df[date_column] = pd.to_datetime(
            chart_df[date_column],
            errors="coerce"
        )

        chart_df = chart_df.dropna(subset=[date_column])

        if not chart_df.empty:
            chart_df["Date Period"] = chart_df[date_column].dt.to_period("M").dt.to_timestamp()

            if useful_numeric_columns:
                numeric_column = useful_numeric_columns[0]

                trend_df = (
                    chart_df
                    .groupby("Date Period")[numeric_column]
                    .mean()
                    .reset_index()
                )

                fig = px.line(
                    trend_df,
                    x="Date Period",
                    y=numeric_column,
                    markers=True,
                    title=f"Average {numeric_column} over time"
                )

                fig.update_layout(
                    xaxis_title=date_column,
                    yaxis_title=f"Average {numeric_column}"
                )

            else:
                trend_df = (
                    chart_df
                    .groupby("Date Period")
                    .size()
                    .reset_index(name="Row Count")
                )

                fig = px.line(
                    trend_df,
                    x="Date Period",
                    y="Row Count",
                    markers=True,
                    title="Number of rows over time"
                )

                fig.update_layout(
                    xaxis_title=date_column,
                    yaxis_title="Number of rows"
                )

            charts.append(
                {
                    "subheader": f"Trend over time using {date_column}",
                    "figure": fig
                }
            )

    return charts