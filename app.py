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

        st.subheader("Dataset Overview")

        rows, columns = df.shape

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Rows", rows)

        with col2:
            st.metric("Columns", columns)

        st.subheader("Preview: First 10 Rows")
        st.dataframe(df.head(10), use_container_width=True)

        if st.button("Go"):
            st.success("Dataset is ready for analysis!")

    except Exception as e:
        st.error("There was a problem loading this CSV file.")
        st.write(e)

else:
    st.info("Please upload a CSV file to begin.")