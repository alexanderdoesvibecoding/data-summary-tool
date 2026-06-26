import streamlit as st
import pandas as pd


st.set_page_config(
    page_title="Data Summarization Tool",
    page_icon="📊",
    layout="wide"
)

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

            # Column type counts
            numeric_columns = df.select_dtypes(include="number").columns.tolist()

            categorical_columns = df.select_dtypes(
                include=["object", "category", "bool"]
            ).columns.tolist()

            # Detect date-like columns
            date_like_columns = []

            for column in df.columns:
                if df[column].dtype == "object":
                    converted_column = pd.to_datetime(
                        df[column],
                        errors="coerce"
                    )

                    valid_dates = converted_column.notna().sum()
                    total_values = df[column].notna().sum()

                    if total_values > 0:
                        date_match_percentage = valid_dates / total_values

                        if date_match_percentage >= 0.8:
                            date_like_columns.append(column)

            number_of_numeric_columns = len(numeric_columns)
            number_of_categorical_columns = len(categorical_columns)
            number_of_date_like_columns = len(date_like_columns)

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

            st.metric("Date-like Columns", number_of_date_like_columns)

            st.subheader("Column Names")
            st.write(list(df.columns))

            if date_like_columns:
                st.subheader("Detected Date-like Columns")
                st.write(date_like_columns)

    except Exception as e:
        st.error("There was a problem loading this CSV file.")
        st.write(e)

else:
    st.info("Please upload a CSV file to begin.")