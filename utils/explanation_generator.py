import pandas as pd

from utils.data_quality import has_possible_outliers


def _format_column_list(column_names: list, max_items: int = 5) -> str:
    if not column_names:
        return ""

    visible_columns = column_names[:max_items]
    column_text = ", ".join(visible_columns)

    remaining_count = len(column_names) - len(visible_columns)

    if remaining_count > 0:
        column_text += f", and {remaining_count} more"

    return column_text


def generate_dataset_overview_explanations(overview: dict) -> list:
    explanations = [
        "Rows are the individual records in your file. Columns are the pieces of information stored for each record.",
        "This overview helps you quickly understand the size and basic shape of the dataset before looking deeper."
    ]

    missing_percentage = overview.get("missing_value_percentage", 0)
    duplicate_row_count = overview.get("duplicate_row_count", 0)
    date_column_count = overview.get("number_of_date_time_columns", 0)

    if missing_percentage >= 20:
        explanations.append(
            f"About {missing_percentage:.1f}% of the values are missing. This is a lot, so be careful when interpreting totals, averages, and charts."
        )
    elif missing_percentage > 0:
        explanations.append(
            f"About {missing_percentage:.1f}% of the values are missing. This may be fine, but results based on those columns may need a quick review."
        )
    else:
        explanations.append(
            "No missing values were found in the basic overview, which usually makes the dataset easier to analyze."
        )

    if duplicate_row_count > 0:
        explanations.append(
            "Duplicate rows can accidentally double-count the same record, especially when you are looking at counts, totals, or averages."
        )

    if date_column_count > 0:
        explanations.append(
            "Because this dataset has at least one date/time column, you may be able to look for trends or changes over time."
        )

    return explanations


def generate_data_quality_explanations(
    df: pd.DataFrame,
    column_summary_df: pd.DataFrame
) -> list:
    explanations = [
        "Data quality notes are not always problems. They are items to review so you can decide whether the results still make sense."
    ]

    number_of_rows = df.shape[0]
    duplicate_row_count = int(df.duplicated().sum())

    columns_with_missing_values = column_summary_df[
        column_summary_df["Missing Values"] > 0
    ]["Column"].tolist()

    if columns_with_missing_values:
        explanations.append(
            "Missing values matter because charts and calculations may skip blank cells. This can change averages, percentages, and totals."
        )

    if duplicate_row_count > 0:
        explanations.append(
            "Duplicate rows may mean the same record appears more than once. Review them so records are not counted twice by mistake."
        )

    numeric_columns = column_summary_df[
        column_summary_df["Detected Type"] == "Numeric"
    ]["Column"].tolist()

    outlier_columns = []

    for column in numeric_columns:
        if has_possible_outliers(df[column]):
            outlier_columns.append(column)

    if outlier_columns:
        explanations.append(
            f"Unusually high or low values were found in {_format_column_list(outlier_columns)}. These values may be real, or they may be entry mistakes, so they are worth checking."
        )

    high_uniqueness_columns = []

    if number_of_rows > 0:
        for column in df.columns:
            unique_count = df[column].nunique(dropna=True)
            uniqueness_percentage = unique_count / number_of_rows

            if uniqueness_percentage >= 0.9 and unique_count > 20:
                high_uniqueness_columns.append(column)

    if high_uniqueness_columns:
        explanations.append(
            f"Columns with many different values, such as {_format_column_list(high_uniqueness_columns)}, can be harder to summarize as groups because most rows are different."
        )

    if len(explanations) == 1:
        explanations.append(
            "No major quality concerns were found by the basic checks. You should still use your own knowledge of the data to confirm the results."
        )

    return explanations


def generate_column_type_explanations(column_summary_df: pd.DataFrame) -> list:
    explanations = [
        "Column types help the app decide which summaries and charts make sense for each column."
    ]

    detected_types = set(column_summary_df["Detected Type"].tolist())

    if "Numeric" in detected_types:
        explanations.append(
            "Numeric columns contain numbers that can usually be averaged, compared, or shown in a histogram."
        )

    if "Categorical" in detected_types:
        explanations.append(
            "Categorical columns represent groups or labels, such as region, product type, status, or department. They work well in bar charts."
        )

    if "Date/time" in detected_types:
        explanations.append(
            "Date/time columns can be used to look for patterns over time, such as busy months or changing activity levels."
        )

    if "Boolean" in detected_types:
        explanations.append(
            "Boolean columns usually mean yes/no or true/false. They are useful for comparing two simple groups."
        )

    if "Text" in detected_types:
        explanations.append(
            "Text columns often contain longer written answers or descriptions. They may need a different kind of review than simple charts."
        )

    if "ID-like" in detected_types:
        explanations.append(
            "ID-like columns identify records, such as customer IDs or order IDs. They are useful for lookup, but usually should not be averaged or treated like normal numbers."
        )

    return explanations


def generate_visualization_overview_explanations(
    numeric_columns: list,
    categorical_columns: list,
    date_columns: list
) -> list:
    explanations = [
        "Visualizations turn columns into charts so patterns are easier to see than they are in a table."
    ]

    if numeric_columns:
        explanations.append(
            "Numeric charts show how numbers are spread out, including common ranges and unusual values."
        )

    if categorical_columns:
        explanations.append(
            "Categorical charts show which groups appear most often. This is helpful for comparing labels or categories."
        )

    if date_columns:
        explanations.append(
            "Date charts show how records change over time. Look for spikes, dips, or steady increases and decreases."
        )

    if len(numeric_columns) >= 2:
        explanations.append(
            "The correlation heatmap compares numeric columns. It can show columns that move together, but it does not prove that one causes another."
        )

    return explanations


def generate_numeric_visualization_explanations(
    column: str,
    numeric_summary: dict
) -> list:
    explanations = [
        f"This histogram shows how values in '{column}' are spread across different ranges.",
        "The average is the overall middle point if all values were balanced out. The median is the middle value after sorting the data."
    ]

    if numeric_summary.get("standard_deviation", 0) > 0:
        explanations.append(
            "Standard deviation describes how spread out the numbers are. A larger value usually means the numbers vary more."
        )

    if numeric_summary.get("missing_count", 0) > 0:
        explanations.append(
            "Blank or invalid values are left out of this numeric summary so they do not distort the chart."
        )

    return explanations


def generate_categorical_visualization_explanations(
    column: str,
    categorical_summary: dict
) -> list:
    explanations = [
        f"This bar chart shows the most common groups or labels in '{column}'.",
        "Longer bars mean that category appears in more rows."
    ]

    most_common_category = categorical_summary.get("most_common_category")

    if most_common_category is not None:
        explanations.append(
            "The most common category can be a useful starting point, but it does not always mean it is the most important category."
        )

    if categorical_summary.get("missing_count", 0) > 0:
        explanations.append(
            "Blank values are left out of this chart so the visible bars only compare known categories."
        )

    return explanations


def generate_date_visualization_explanations(
    column: str,
    date_summary: dict
) -> list:
    explanations = [
        f"This chart groups records by time using '{column}'.",
        "Look for months or periods where the line rises, falls, or has sudden spikes."
    ]

    if date_summary.get("missing_count", 0) > 0:
        explanations.append(
            "Blank or invalid dates are left out because they cannot be placed on the timeline."
        )

    return explanations


def generate_correlation_explanations(correlation_fig_exists: bool) -> list:
    if correlation_fig_exists:
        return [
            "Correlation compares numeric columns to see whether they tend to move together.",
            "Values close to 1 or -1 show a stronger relationship. Values close to 0 show a weaker relationship.",
            "A strong relationship does not prove cause and effect. It only shows that the columns change together in this dataset."
        ]

    return [
        "A correlation heatmap is only shown when there are at least two numeric columns with usable values."
    ]


def generate_key_insights_explanations() -> list:
    return [
        "Key insights are quick rule-based observations to help you decide what to review first.",
        "They are not AI-generated and they should not be treated as final conclusions. Use them as a starting point for your own review."
    ]