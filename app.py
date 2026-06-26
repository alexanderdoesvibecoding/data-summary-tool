import streamlit as st
import pandas as pd


st.set_page_config(
    page_title="Data Summarization Tool",
    page_icon="📊",
    layout="wide"
)


def detect_column_type(series: pd.Series) -> str:
    """
    Detects a beginner-friendly column type.

    Possible types:
    - Numeric
    - Categorical
    - Date/time
    - Boolean
    - Text
    - ID-like
    """

    non_missing_series = series.dropna()
    total_non_missing = len(non_missing_series)

    if total_non_missing == 0:
        return "Text"

    unique_count = non_missing_series.nunique()
    unique_percentage = unique_count / total_non_missing

    column_name = series.name.lower()

    # Boolean columns
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

    # Date/time columns
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

    # Numeric columns
    if pd.api.types.is_numeric_dtype(series):
        # Numeric ID-like columns
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

    # ID-like text columns
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

    # Categorical columns
    if unique_count <= 20 or unique_percentage <= 0.2:
        return "Categorical"

    # Longer free-form text columns
    average_text_length = non_missing_series.astype(str).str.len().mean()

    if average_text_length >= 30:
        return "Text"

    # Default object/string columns to categorical
    return "Categorical"


def has_possible_outliers(series: pd.Series) -> bool:
    """
    Checks for possible numeric outliers using the IQR method.

    This is a common beginner-friendly rule:
    values far below Q1 or far above Q3 are flagged as possible outliers.
    """

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
    """
    Creates plain-English data quality notes for non-technical users.
    """

    notes = []

    number_of_rows = df.shape[0]
    duplicate_row_count = df.duplicated().sum()

    # Columns with missing values
    columns_with_missing_values = column_summary_df[
        column_summary_df["Missing Values"] > 0
    ]

    if not columns_with_missing_values.empty:
        column_names = columns_with_missing_values["Column"].tolist()

        notes.append(
            f"Some columns have missing values: {', '.join(column_names)}. "
            "This means some rows do not have an answer or value for those columns."
        )

    # Duplicate rows
    if duplicate_row_count > 0:
        notes.append(
            f"There are {duplicate_row_count} duplicate rows. "
            "Duplicate rows may represent repeated records, so you may want to review them before analysis."
        )

    # Columns with only one unique value
    single_value_columns = column_summary_df[
        column_summary_df["Unique Values"] == 1
    ]["Column"].tolist()

    if single_value_columns:
        notes.append(
            f"These columns only contain one unique value: {', '.join(single_value_columns)}. "
            "They may not be very useful for comparisons because every row has the same value."
        )

    # Possible ID columns
    possible_id_columns = column_summary_df[
        column_summary_df["Detected Type"] == "ID-like"
    ]["Column"].tolist()

    if possible_id_columns:
        notes.append(
            f"These columns look like possible ID columns: {', '.join(possible_id_columns)}. "
            "ID columns are useful for identifying records, but they usually should not be averaged, summed, or charted like normal numbers."
        )

    # Numeric columns with possible outliers
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

    # Columns with very high uniqueness
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


st.title("📊 Data Summarization and Visualization Tool")
st.write("Upload a CSV file to get started.")

uploaded_file = st.file_uploader(
    "Choose a CSV file",
    type=["csv"]
)

if uploaded_file is not None:
    st.subheader("Uploaded File")
    st.write(f"**File name:** {uploaded_file.name}")

    try:
        df = pd.read_csv(uploaded_file)

        st.subheader("Preview: First 10 Rows")
        st.dataframe(df.head(10), use_container_width=True)

        if st.button("Go"):
            st.success("Dataset is ready for analysis!")

            st.header("Dataset Overview")

            # Basic dataset shape
            number_of_rows = df.shape[0]
            number_of_columns = df.shape[1]

            # Duplicate rows
            duplicate_row_count = df.duplicated().sum()

            # Missing value percentage across the whole dataset
            total_cells = number_of_rows * number_of_columns
            missing_cells = df.isnull().sum().sum()

            if total_cells > 0:
                missing_value_percentage = (missing_cells / total_cells) * 100
            else:
                missing_value_percentage = 0

            # Detect column types
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

            column_summary_df = pd.DataFrame(column_summary)

            number_of_numeric_columns = (
                column_summary_df["Detected Type"] == "Numeric"
            ).sum()

            number_of_categorical_columns = (
                column_summary_df["Detected Type"] == "Categorical"
            ).sum()

            number_of_date_time_columns = (
                column_summary_df["Detected Type"] == "Date/time"
            ).sum()

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Rows", number_of_rows)

            with col2:
                st.metric("Columns", number_of_columns)

            with col3:
                st.metric("Duplicate Rows", duplicate_row_count)

            col4, col5, col6 = st.columns(3)

            with col4:
                st.metric(
                    "Missing Values",
                    f"{missing_value_percentage:.2f}%"
                )

            with col5:
                st.metric("Numeric Columns", number_of_numeric_columns)

            with col6:
                st.metric("Categorical Columns", number_of_categorical_columns)

            st.metric("Date/time Columns", number_of_date_time_columns)

            st.subheader("Column Names")
            st.write(list(df.columns))

            st.subheader("Column Type Detection")
            st.write(
                "Each column is automatically classified to help decide what kind of analysis or visualization may fit best."
            )

            st.dataframe(
                column_summary_df,
                use_container_width=True,
                hide_index=True
            )

            st.subheader("Data Quality Notes")
            st.write(
                "These notes point out things that may be worth reviewing before analyzing the dataset."
            )

            data_quality_notes = generate_data_quality_notes(
                df,
                column_summary_df
            )

            for note in data_quality_notes:
                st.info(note)

    except Exception as e:
        st.error("There was a problem loading this CSV file.")
        st.write(e)

else:
    st.info("Please upload a CSV file to begin.")