import pandas as pd


def has_possible_outliers(series: pd.Series) -> bool:
    numeric_series = pd.to_numeric(series, errors="coerce").dropna()

    if len(numeric_series) < 4:
        return False

    q1 = numeric_series.quantile(0.25)
    q3 = numeric_series.quantile(0.75)
    iqr = q3 - q1

    if iqr == 0:
        return False

    lower_limit = q1 - 1.5 * iqr
    upper_limit = q3 + 1.5 * iqr

    outlier_count = (
        (numeric_series < lower_limit) | (numeric_series > upper_limit)
    ).sum()

    return outlier_count > 0


def generate_data_quality_notes(df: pd.DataFrame, column_summary_df: pd.DataFrame) -> list:
    notes = []

    number_of_rows = df.shape[0]
    duplicate_row_count = df.duplicated().sum()

    columns_with_missing_values = column_summary_df[
        column_summary_df["Missing Values"] > 0
    ]

    if not columns_with_missing_values.empty:
        column_names = columns_with_missing_values["Column"].tolist()

        notes.append(
            f"Some columns have missing values: {', '.join(column_names)}. "
            "This means some rows do not have an answer or value for those columns."
        )

    if duplicate_row_count > 0:
        notes.append(
            f"There are {duplicate_row_count} duplicate rows. "
            "Duplicate rows may represent repeated records, so you may want to review them before analysis."
        )

    single_value_columns = column_summary_df[
        column_summary_df["Unique Values"] == 1
    ]["Column"].tolist()

    if single_value_columns:
        notes.append(
            f"These columns only contain one unique value: {', '.join(single_value_columns)}. "
            "They may not be very useful for comparisons because every row has the same value."
        )

    possible_id_columns = column_summary_df[
        column_summary_df["Detected Type"] == "ID-like"
    ]["Column"].tolist()

    if possible_id_columns:
        notes.append(
            f"These columns look like possible ID columns: {', '.join(possible_id_columns)}. "
            "ID columns are useful for identifying records, but they usually should not be averaged, summed, or charted like normal numbers."
        )

    numeric_columns = column_summary_df[
        column_summary_df["Detected Type"] == "Numeric"
    ]["Column"].tolist()

    numeric_columns_with_outliers = []

    for column in numeric_columns:
        if has_possible_outliers(df[column]):
            numeric_columns_with_outliers.append(column)

    if numeric_columns_with_outliers:
        notes.append(
            f"These numeric columns may contain unusual high or low values: {', '.join(numeric_columns_with_outliers)}. "
            "These values may be correct, but they are worth checking because they can strongly affect averages and charts."
        )

    high_uniqueness_columns = []

    if number_of_rows > 0:
        for column in df.columns:
            unique_count = df[column].nunique(dropna=True)
            uniqueness_percentage = unique_count / number_of_rows

            if (
                uniqueness_percentage >= 0.9
                and unique_count > 20
                and column not in possible_id_columns
            ):
                high_uniqueness_columns.append(column)

    if high_uniqueness_columns:
        notes.append(
            f"These columns have a very high number of unique values: {', '.join(high_uniqueness_columns)}. "
            "They may be harder to group or summarize because most rows have their own separate value."
        )

    if not notes:
        notes.append(
            "No major data quality issues were found from these basic checks."
        )

    return notes