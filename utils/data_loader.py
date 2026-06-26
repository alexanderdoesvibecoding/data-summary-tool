import pandas as pd


def load_csv(uploaded_file) -> pd.DataFrame:
    return pd.read_csv(uploaded_file)


def get_dataset_overview(df: pd.DataFrame, column_summary_df: pd.DataFrame) -> dict:
    number_of_rows = df.shape[0]
    number_of_columns = df.shape[1]
    duplicate_row_count = df.duplicated().sum()

    total_cells = number_of_rows * number_of_columns
    missing_cells = df.isnull().sum().sum()

    if total_cells > 0:
        missing_value_percentage = (missing_cells / total_cells) * 100
    else:
        missing_value_percentage = 0

    number_of_numeric_columns = (
        column_summary_df["Detected Type"] == "Numeric"
    ).sum()

    number_of_categorical_columns = (
        column_summary_df["Detected Type"] == "Categorical"
    ).sum()

    number_of_date_time_columns = (
        column_summary_df["Detected Type"] == "Date/time"
    ).sum()

    return {
        "number_of_rows": number_of_rows,
        "number_of_columns": number_of_columns,
        "duplicate_row_count": duplicate_row_count,
        "missing_value_percentage": missing_value_percentage,
        "number_of_numeric_columns": number_of_numeric_columns,
        "number_of_categorical_columns": number_of_categorical_columns,
        "number_of_date_time_columns": number_of_date_time_columns
    }