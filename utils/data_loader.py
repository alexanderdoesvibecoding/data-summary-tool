import pandas as pd


SUPPORTED_FILE_TYPES = ["csv", "xlsx", "xls"]


def get_file_extension(file_name: str) -> str:
    return file_name.split(".")[-1].lower()


def get_excel_sheet_names(uploaded_file) -> list:
    uploaded_file.seek(0)

    try:
        excel_file = pd.ExcelFile(uploaded_file)
        return excel_file.sheet_names

    except Exception as exc:
        raise ValueError(
            "There was a problem reading the Excel sheets. "
            "Please make sure the file is a valid Excel file."
        ) from exc

    finally:
        uploaded_file.seek(0)


def load_uploaded_file(uploaded_file, sheet_name: str | None = None) -> pd.DataFrame:
    file_extension = get_file_extension(uploaded_file.name)

    uploaded_file.seek(0)

    try:
        if file_extension == "csv":
            return pd.read_csv(uploaded_file)

        if file_extension in ["xlsx", "xls"]:
            return pd.read_excel(
                uploaded_file,
                sheet_name=sheet_name
            )

        raise ValueError(
            "Unsupported file type. Please upload a CSV or Excel file."
        )

    except ValueError:
        raise

    except Exception as exc:
        raise ValueError(
            "There was a problem reading this file. "
            "Please make sure it is a valid CSV or Excel file."
        ) from exc

    finally:
        uploaded_file.seek(0)


def load_csv(uploaded_file) -> pd.DataFrame:
    uploaded_file.seek(0)
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