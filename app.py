import streamlit as st

from utils.chart_generator import (
    generate_categorical_bar_chart,
    generate_categorical_summary,
    generate_correlation_heatmap,
    generate_date_trend_chart,
    generate_numeric_histogram,
    generate_numeric_summary,
    get_categorical_columns,
    get_date_columns,
    get_numeric_columns,
)
from utils.data_loader import (
    get_dataset_overview,
    get_excel_sheet_names,
    get_file_extension,
    load_uploaded_file,
)
from utils.data_quality import generate_data_quality_notes
from utils.insight_generator import generate_key_insights
from utils.type_detection import create_column_summary


st.set_page_config(
    page_title="Data Summarization Tool",
    page_icon="📊",
    layout="wide"
)


st.title("📊 Data Summarization and Visualization Tool")
st.write("Upload a CSV or Excel file to get started.")

uploaded_file = st.file_uploader(
    "Choose a CSV or Excel file",
    type=["csv", "xlsx", "xls"]
)

if uploaded_file is not None:
    if st.session_state.get("uploaded_file_name") != uploaded_file.name:
        st.session_state["uploaded_file_name"] = uploaded_file.name
        st.session_state["analysis_started"] = False
        st.session_state["selected_sheet_name"] = None

    st.subheader("Uploaded File")
    st.write(f"**File name:** {uploaded_file.name}")

    try:
        file_extension = get_file_extension(uploaded_file.name)
        selected_sheet_name = None

        if file_extension in ["xlsx", "xls"]:
            sheet_names = get_excel_sheet_names(uploaded_file)

            if not sheet_names:
                st.error(
                    "This Excel file does not appear to contain any sheets. "
                    "Please upload a different CSV or Excel file."
                )
                st.stop()

            selected_sheet_name = st.selectbox(
                "Choose an Excel sheet to analyze",
                sheet_names
            )

            st.session_state["selected_sheet_name"] = selected_sheet_name

        df = load_uploaded_file(
            uploaded_file,
            sheet_name=selected_sheet_name
        )

        if df.empty:
            if selected_sheet_name:
                st.warning(
                    f"The selected sheet, '{selected_sheet_name}', is empty. "
                    "Please choose a different sheet or upload a file with data."
                )
            else:
                st.warning(
                    "This file appears to be empty. Please upload a file with data."
                )

            st.stop()

        st.subheader("Preview: First 10 Rows")

        if selected_sheet_name:
            st.write(f"Currently analyzing sheet: **{selected_sheet_name}**")

        st.dataframe(df.head(10), use_container_width=True)

        if st.button("Go"):
            st.session_state["analysis_started"] = True

        if st.session_state.get("analysis_started", False):
            st.success("Dataset is ready for analysis!")

            st.header("Dataset Overview")

            column_summary_df = create_column_summary(df)
            overview = get_dataset_overview(df, column_summary_df)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Rows", overview["number_of_rows"])

            with col2:
                st.metric("Columns", overview["number_of_columns"])

            with col3:
                st.metric("Duplicate Rows", overview["duplicate_row_count"])

            col4, col5, col6 = st.columns(3)

            with col4:
                st.metric(
                    "Missing Values",
                    f"{overview['missing_value_percentage']:.2f}%"
                )

            with col5:
                st.metric("Numeric Columns", overview["number_of_numeric_columns"])

            with col6:
                st.metric("Categorical Columns", overview["number_of_categorical_columns"])

            st.metric("Date/time Columns", overview["number_of_date_time_columns"])

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

            st.header("Visualizations")
            st.write(
                "Choose variables below to explore specific parts of the dataset. "
                "Charts update automatically when you change a selection."
            )

            numeric_columns = get_numeric_columns(df, column_summary_df)
            categorical_columns = get_categorical_columns(df, column_summary_df)
            date_columns = get_date_columns(column_summary_df)

            st.subheader("Numeric Column Analysis")

            if numeric_columns:
                selected_numeric_column = st.selectbox(
                    "Choose a numeric column to visualize",
                    numeric_columns
                )

                numeric_summary = generate_numeric_summary(
                    df,
                    selected_numeric_column
                )

                if numeric_summary["non_missing_count"] > 0:
                    if numeric_summary["missing_count"] > 0:
                        st.info(
                            f"{numeric_summary['missing_count']} missing value(s) were excluded from this chart and summary."
                        )

                    metric_col1, metric_col2, metric_col3 = st.columns(3)

                    with metric_col1:
                        st.metric("Average", f"{numeric_summary['mean']:.2f}")

                    with metric_col2:
                        st.metric("Median", f"{numeric_summary['median']:.2f}")

                    with metric_col3:
                        st.metric(
                            "Standard Deviation",
                            f"{numeric_summary['standard_deviation']:.2f}"
                        )

                    metric_col4, metric_col5, metric_col6 = st.columns(3)

                    with metric_col4:
                        st.metric("Minimum", f"{numeric_summary['minimum']:.2f}")

                    with metric_col5:
                        st.metric("Maximum", f"{numeric_summary['maximum']:.2f}")

                    with metric_col6:
                        st.metric("Values Used", numeric_summary["non_missing_count"])

                    numeric_fig = generate_numeric_histogram(
                        df,
                        selected_numeric_column
                    )

                    st.plotly_chart(
                        numeric_fig,
                        use_container_width=True
                    )

                else:
                    st.info(
                        f"{selected_numeric_column} does not have any non-missing numeric values to visualize."
                    )

            else:
                st.info(
                    "No numeric columns were found, so there is no numeric histogram to show."
                )

            st.subheader("Categorical Column Analysis")

            if categorical_columns:
                selected_categorical_column = st.selectbox(
                    "Choose a categorical column to visualize",
                    categorical_columns
                )

                categorical_summary = generate_categorical_summary(
                    df,
                    selected_categorical_column
                )

                if categorical_summary["non_missing_count"] > 0:
                    if categorical_summary["missing_count"] > 0:
                        st.info(
                            f"{categorical_summary['missing_count']} missing value(s) were excluded from this chart and summary."
                        )

                    st.write(
                        f"The most common category is **{categorical_summary['most_common_category']}**, "
                        f"which appears in **{categorical_summary['most_common_percentage']:.2f}%** "
                        "of the non-missing rows."
                    )

                    categorical_fig = generate_categorical_bar_chart(
                        df,
                        selected_categorical_column
                    )

                    st.plotly_chart(
                        categorical_fig,
                        use_container_width=True
                    )

                else:
                    st.info(
                        f"{selected_categorical_column} does not have any non-missing values to visualize."
                    )

            else:
                st.info(
                    "No categorical columns were found, so there is no categorical bar chart to show."
                )

            st.subheader("Date/Time Column Analysis")

            if date_columns:
                selected_date_column = st.selectbox(
                    "Choose a date column to visualize",
                    date_columns
                )

                date_fig, date_summary = generate_date_trend_chart(
                    df,
                    selected_date_column
                )

                if date_fig is not None:
                    if date_summary["missing_count"] > 0:
                        st.info(
                            f"{date_summary['missing_count']} missing or invalid date value(s) were excluded from this chart."
                        )

                    st.plotly_chart(
                        date_fig,
                        use_container_width=True
                    )

                else:
                    st.info(
                        f"{selected_date_column} does not have enough valid date values to create a trend chart."
                    )

            else:
                st.info(
                    "No date/time columns were found, so there is no date trend chart to show."
                )

            st.subheader("Correlation Between Numeric Columns")

            correlation_fig = generate_correlation_heatmap(
                df,
                numeric_columns
            )

            if correlation_fig is not None:
                st.plotly_chart(
                    correlation_fig,
                    use_container_width=True
                )
            else:
                st.info(
                    "A correlation heatmap needs at least 2 numeric columns with usable values."
                )

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

    except ValueError as e:
        st.error(str(e))

    except Exception:
        st.error(
            "There was a problem reading this file. "
            "Please make sure it is a valid CSV or Excel file and try again."
        )

else:
    st.info("Please upload a CSV or Excel file to begin.")