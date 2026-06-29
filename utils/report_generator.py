import pandas as pd


def _format_number(value) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"

    return str(value)


def _markdown_table_from_dataframe(df: pd.DataFrame) -> str:
    if df.empty:
        return "No column type information is available."

    columns = list(df.columns)

    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"

    rows = []

    for _, row in df.iterrows():
        row_values = []

        for column in columns:
            value = row[column]

            if pd.isna(value):
                row_values.append("")
            else:
                row_values.append(str(value))

        rows.append("| " + " | ".join(row_values) + " |")

    return "\n".join([header, separator] + rows)


def _format_notes_list(items: list, empty_message: str) -> str:
    if not items:
        return f"- {empty_message}"

    return "\n".join([f"- {item}" for item in items])


def _build_visualization_descriptions(selected_visualizations: dict) -> str:
    numeric_column = selected_visualizations.get("numeric_column")
    categorical_column = selected_visualizations.get("categorical_column")
    date_column = selected_visualizations.get("date_column")
    correlation_heatmap_included = selected_visualizations.get(
        "correlation_heatmap_included",
        False
    )
    correlation_columns = selected_visualizations.get(
        "correlation_columns",
        []
    )

    report_sections = []

    if numeric_column:
        report_sections.append(
            "### Numeric visualization\n"
            f"- Selected column: **{numeric_column}**\n"
            "- Description: This histogram shows how the values are spread out. "
            "It can help you see common value ranges, unusual values, and whether the data is clustered or spread widely."
        )
    else:
        report_sections.append(
            "### Numeric visualization\n"
            "- No numeric column was selected or available."
        )

    if categorical_column:
        report_sections.append(
            "### Categorical visualization\n"
            f"- Selected column: **{categorical_column}**\n"
            "- Description: This bar chart shows the 10 most common categories. "
            "It can help you quickly see which groups appear most often in the dataset."
        )
    else:
        report_sections.append(
            "### Categorical visualization\n"
            "- No categorical column was selected or available."
        )

    if date_column:
        report_sections.append(
            "### Date/time visualization\n"
            f"- Selected column: **{date_column}**\n"
            "- Description: This trend chart shows how many records appear over time. "
            "It can help you spot increases, decreases, or busy time periods."
        )
    else:
        report_sections.append(
            "### Date/time visualization\n"
            "- No date/time column was selected or available."
        )

    if correlation_heatmap_included:
        columns_text = ", ".join(correlation_columns)

        report_sections.append(
            "### Correlation heatmap\n"
            "- Included automatically because the dataset has at least 2 usable numeric columns.\n"
            f"- Numeric columns reviewed: **{columns_text}**\n"
            "- Description: This heatmap compares numeric columns to show which ones tend to move together. "
            "A strong correlation does not prove that one column causes another."
        )
    else:
        report_sections.append(
            "### Correlation heatmap\n"
            "- Not included because the dataset does not have at least 2 usable numeric columns."
        )

    return "\n\n".join(report_sections)


def generate_markdown_report(
    file_name: str,
    sheet_name: str | None,
    overview: dict,
    data_quality_notes: list,
    column_summary_df: pd.DataFrame,
    key_insights: list,
    selected_visualizations: dict
) -> str:
    sheet_text = f"\n**Excel sheet analyzed:** {sheet_name}\n" if sheet_name else ""

    column_type_summary = _markdown_table_from_dataframe(column_summary_df)
    data_quality_section = _format_notes_list(
        data_quality_notes,
        "No major data quality notes were found."
    )
    insights_section = _format_notes_list(
        key_insights,
        "No key insights were generated for this dataset."
    )
    visualization_section = _build_visualization_descriptions(
        selected_visualizations
    )

    report = f"""# Data Summary Report

This report gives a beginner-friendly summary of the uploaded dataset.

**File analyzed:** {file_name}
{sheet_text}
---

## Dataset Overview

- **Rows:** {_format_number(overview.get("number_of_rows", 0))}
- **Columns:** {_format_number(overview.get("number_of_columns", 0))}
- **Duplicate rows:** {_format_number(overview.get("duplicate_row_count", 0))}
- **Missing values:** {_format_number(overview.get("missing_value_percentage", 0))}%
- **Numeric columns:** {_format_number(overview.get("number_of_numeric_columns", 0))}
- **Categorical columns:** {_format_number(overview.get("number_of_categorical_columns", 0))}
- **Date/time columns:** {_format_number(overview.get("number_of_date_time_columns", 0))}

## Data Quality Notes

{data_quality_section}

## Column Type Summary

{column_type_summary}

## Key Insights

{insights_section}

## Selected Visualizations

{visualization_section}

---

## Notes

This report does not include chart images yet. It summarizes the selected visualizations in plain English so the results are easy to review and share.
"""

    return report