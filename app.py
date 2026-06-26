import streamlit as st

from utils.chart_generator import generate_automatic_charts
from utils.data_loader import get_dataset_overview, load_csv
from utils.data_quality import generate_data_quality_notes
from utils.insight_generator import generate_key_insights
from utils.type_detection import create_column_summary


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
        df = load_csv(uploaded_file)

        st.subheader("Preview: First 10 Rows")
        st.dataframe(df.head(10), use_container_width=True)

        if st.button("Go"):
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

            st.header("Automatic Visualizations")
            st.write(
                "The app chooses a small number of useful charts so the page does not get overcrowded."
            )

            charts = generate_automatic_charts(df, column_summary_df)

            if charts:
                for chart in charts:
                    st.subheader(chart["subheader"])
                    st.plotly_chart(chart["figure"], use_container_width=True)
            else:
                st.info(
                    "No automatic charts were created because the app did not find enough suitable numeric, categorical, or date/time columns."
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

    except Exception as e:
        st.error("There was a problem loading this CSV file.")
        st.write(e)

else:
    st.info("Please upload a CSV file to begin.")