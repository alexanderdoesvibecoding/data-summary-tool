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

    except Exception as e:
        st.error("There was a problem loading this CSV file.")
        st.write(e)

else:
    st.info("Please upload a CSV file to begin.")