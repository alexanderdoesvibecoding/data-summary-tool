import streamlit as st
import pandas as pd
import plotly.express as px


st.set_page_config(
    page_title="Data Summarization Tool",
    page_icon="📊",
    layout="wide"
)


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


def show_automatic_visualizations(
    df: pd.DataFrame,
    column_summary_df: pd.DataFrame
) -> None:
    st.header("Automatic Visualizations")

    st.write(
        "The app chooses a small number of useful charts so the page does not get overcrowded."
    )

    numeric_columns = column_summary_df[
        column_summary_df["Detected Type"] == "Numeric"
    ]["Column"].tolist()

    categorical_columns = column_summary_df[
        column_summary_df["Detected Type"] == "Categorical"
    ]["Column"].tolist()

    date_columns = column_summary_df[
        column_summary_df["Detected Type"] == "Date/time"
    ]["Column"].tolist()

    charts_created = 0

    # Histograms for up to 2 useful numeric columns
    useful_numeric_columns = []

    for column in numeric_columns:
        if df[column].nunique(dropna=True) > 1:
            useful_numeric_columns.append(column)

    for column in useful_numeric_columns[:2]:
        st.subheader(f"Distribution of {column}")

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

        st.plotly_chart(fig, use_container_width=True)
        charts_created += 1

    # Bar charts for up to 2 useful categorical columns
    useful_categorical_columns = []

    for column in categorical_columns:
        unique_count = df[column].nunique(dropna=True)

        if 2 <= unique_count <= 50:
            useful_categorical_columns.append(column)

    for column in useful_categorical_columns[:2]:
        st.subheader(f"Top categories in {column}")

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

        st.plotly_chart(fig, use_container_width=True)
        charts_created += 1

    # Correlation heatmap if there are at least 2 numeric columns
    if len(useful_numeric_columns) >= 2:
        st.subheader("Correlation Between Numeric Columns")

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

        st.plotly_chart(fig, use_container_width=True)
        charts_created += 1

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
            st.subheader(f"Trend over time using {date_column}")

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

            st.plotly_chart(fig, use_container_width=True)
            charts_created += 1

    if charts_created == 0:
        st.info(
            "No automatic charts were created because the app did not find enough suitable numeric, categorical, or date/time columns."
        )

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

            number_of_rows = df.shape[0]
            number_of_columns = df.shape[1]

            duplicate_row_count = df.duplicated().sum()

            total_cells = number_of_rows * number_of_columns
            missing_cells = df.isnull().sum().sum()

            if total_cells > 0:
                missing_value_percentage = (missing_cells / total_cells) * 100
            else:
                missing_value_percentage = 0

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

            show_automatic_visualizations(df, column_summary_df)

            st.subheader("Key Insights")
            st.write(
                "These insights are created using simple rules, not AI. "
                "They are meant to help you quickly understand patterns worth reviewing."
            )

            key_insights = generate_key_insights(
                df,
                column_summary_df
            )

            for insight in key_insights:
                st.success(insight)

    except Exception as e:
        st.error("There was a problem loading this CSV file.")
        st.write(e)

else:
    st.info("Please upload a CSV file to begin.")