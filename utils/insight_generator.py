import pandas as pd


def generate_key_insights(df: pd.DataFrame, column_summary_df: pd.DataFrame) -> list:
    """
    Generates plain-English, rule-based insights about the dataset.
    This does not use AI. It only uses simple checks and calculations.
    """

    insights = []

    number_of_rows = df.shape[0]
    duplicate_row_count = df.duplicated().sum()

    numeric_columns = column_summary_df[
        column_summary_df["Detected Type"] == "Numeric"
    ]["Column"].tolist()

    categorical_columns = column_summary_df[
        column_summary_df["Detected Type"] == "Categorical"
    ]["Column"].tolist()

    # Missing values insight
    columns_with_missing_values = column_summary_df[
        column_summary_df["Missing Values"] > 0
    ]

    if not columns_with_missing_values.empty:
        missing_column_count = len(columns_with_missing_values)

        insights.append(
            f"{missing_column_count} column(s) have missing values. "
            "This means some rows are incomplete, so results based on those columns may need extra review."
        )

    # Duplicate rows insight
    if duplicate_row_count > 0:
        insights.append(
            f"The dataset contains {duplicate_row_count} duplicate row(s). "
            "These may be repeated records and could affect counts, totals, and averages."
        )

    # Numeric skew insights
    for column in numeric_columns[:3]:
        numeric_series = pd.to_numeric(df[column], errors="coerce").dropna()

        if len(numeric_series) >= 10:
            skew_value = numeric_series.skew()

            if skew_value >= 1:
                insights.append(
                    f"The numeric column '{column}' appears to be right-skewed. "
                    "This means most values are lower, with a smaller number of unusually high values."
                )
            elif skew_value <= -1:
                insights.append(
                    f"The numeric column '{column}' appears to be left-skewed. "
                    "This means most values are higher, with a smaller number of unusually low values."
                )

    # Most common category insights
    for column in categorical_columns[:3]:
        value_counts = df[column].dropna().astype(str).value_counts()

        if not value_counts.empty:
            most_common_value = value_counts.index[0]
            most_common_count = value_counts.iloc[0]
            most_common_percentage = (most_common_count / number_of_rows) * 100

            insights.append(
                f"In '{column}', the most common value is '{most_common_value}', "
                f"which appears in {most_common_percentage:.1f}% of rows."
            )

    # Strong correlation insights
    if len(numeric_columns) >= 2:
        numeric_df = df[numeric_columns].apply(
            pd.to_numeric,
            errors="coerce"
        )

        correlation_df = numeric_df.corr()

        strong_correlations = []

        for i in range(len(correlation_df.columns)):
            for j in range(i + 1, len(correlation_df.columns)):
                column_a = correlation_df.columns[i]
                column_b = correlation_df.columns[j]
                correlation_value = correlation_df.loc[column_a, column_b]

                if pd.notna(correlation_value) and abs(correlation_value) >= 0.7:
                    strong_correlations.append(
                        (column_a, column_b, correlation_value)
                    )

        for column_a, column_b, correlation_value in strong_correlations[:3]:
            if correlation_value > 0:
                direction = "positively associated with"
            else:
                direction = "negatively associated with"

            insights.append(
                f"'{column_a}' appears to be strongly {direction} '{column_b}'. "
                "This does not mean one causes the other, but the two columns tend to move together."
            )

    if not insights:
        insights.append(
            "No major automatic insights were found from these basic rule-based checks."
        )

    return insights