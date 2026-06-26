import pandas as pd


def detect_column_type(series: pd.Series) -> str:
    non_missing_series = series.dropna()
    total_non_missing = len(non_missing_series)

    if total_non_missing == 0:
        return "Text"

    unique_count = non_missing_series.nunique()
    unique_percentage = unique_count / total_non_missing
    column_name = series.name.lower()

    if pd.api.types.is_bool_dtype(series):
        return "Boolean"

    boolean_like_values = set(
        non_missing_series.astype(str).str.lower().str.strip().unique()
    )

    common_boolean_values = {
        "true",
        "false",
        "yes",
        "no",
        "y",
        "n",
        "0",
        "1"
    }

    if boolean_like_values.issubset(common_boolean_values) and unique_count <= 2:
        return "Boolean"

    if pd.api.types.is_datetime64_any_dtype(series):
        return "Date/time"

    if pd.api.types.is_object_dtype(series):
        converted_dates = pd.to_datetime(
            non_missing_series,
            errors="coerce"
        )

        date_match_percentage = converted_dates.notna().sum() / total_non_missing

        if date_match_percentage >= 0.8:
            return "Date/time"

    if pd.api.types.is_numeric_dtype(series):
        if (
            unique_percentage > 0.9
            and (
                "id" in column_name
                or column_name.endswith("_id")
                or column_name.endswith("id")
            )
        ):
            return "ID-like"

        return "Numeric"

    if (
        unique_percentage > 0.9
        and (
            "id" in column_name
            or column_name.endswith("_id")
            or column_name.endswith("id")
            or "uuid" in column_name
            or "code" in column_name
        )
    ):
        return "ID-like"

    if unique_count <= 20 or unique_percentage <= 0.2:
        return "Categorical"

    average_text_length = non_missing_series.astype(str).str.len().mean()

    if average_text_length >= 30:
        return "Text"

    return "Categorical"


def create_column_summary(df: pd.DataFrame) -> pd.DataFrame:
    column_summary = []

    for column in df.columns:
        detected_type = detect_column_type(df[column])
        missing_values = df[column].isnull().sum()
        unique_values = df[column].nunique()

        column_summary.append(
            {
                "Column": column,
                "Detected Type": detected_type,
                "Missing Values": missing_values,
                "Unique Values": unique_values
            }
        )

    return pd.DataFrame(column_summary)