"""Core Excel generation functions using pandas and matplotlib for charts."""

import io
import pandas as pd
from pathlib import Path
from typing import Optional, Union, List, Dict, Any
from datetime import datetime, timedelta
import random

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

# Color palette for charts
CHART_COLORS = [
    '#36A2EB', '#FF6384', '#FFCE56', '#4BC0C0', '#9966FF',
    '#FF9F40', '#7CBA3F', '#EA5545', '#27AEEF', '#B33DC6'
]


def generate_sample_data(rows: int = 100) -> pd.DataFrame:
    """Generate sample sales data for demonstration purposes.

    Args:
        rows: Number of rows to generate.

    Returns:
        DataFrame with sample sales data.
    """
    random.seed(42)

    categories = ["Electronics", "Clothing", "Food", "Books", "Home & Garden"]
    regions = ["North", "South", "East", "West", "Central"]
    products = {
        "Electronics": ["Laptop", "Phone", "Tablet", "Headphones", "Camera"],
        "Clothing": ["Shirt", "Pants", "Jacket", "Shoes", "Hat"],
        "Food": ["Snacks", "Beverages", "Frozen", "Dairy", "Produce"],
        "Books": ["Fiction", "Non-Fiction", "Technical", "Children", "Comics"],
        "Home & Garden": ["Furniture", "Tools", "Decor", "Plants", "Lighting"],
    }

    data = []
    base_date = datetime(2024, 1, 1)

    for _ in range(rows):
        category = random.choice(categories)
        product = random.choice(products[category])
        region = random.choice(regions)
        date = base_date + timedelta(days=random.randint(0, 364))
        quantity = random.randint(1, 50)
        unit_price = round(random.uniform(10, 500), 2)
        revenue = round(quantity * unit_price, 2)

        data.append({
            "Date": date,
            "Category": category,
            "Product": product,
            "Region": region,
            "Quantity": quantity,
            "Unit_Price": unit_price,
            "Revenue": revenue,
        })

    return pd.DataFrame(data)


def create_data_sheet(
    df: pd.DataFrame,
    writer: pd.ExcelWriter,
    sheet_name: str = "Data",
    format_as_table: bool = True,
) -> None:
    """Write a DataFrame to an Excel sheet.

    Args:
        df: DataFrame to write.
        writer: ExcelWriter object.
        sheet_name: Name of the sheet.
        format_as_table: Whether to format as Excel table.
    """
    df.to_excel(writer, sheet_name=sheet_name, index=False)

    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    # Auto-adjust column widths
    for idx, col in enumerate(df.columns):
        max_length = max(
            df[col].astype(str).map(len).max(),
            len(str(col))
        ) + 2
        worksheet.set_column(idx, idx, min(max_length, 50))


def create_pivot_table(
    df: pd.DataFrame,
    writer: pd.ExcelWriter,
    sheet_name: str = "Pivot",
    values: str = "Revenue",
    index: Union[str, List[str]] = "Category",
    columns: Optional[Union[str, List[str]]] = "Region",
    aggfunc: str = "sum",
) -> pd.DataFrame:
    """Create a pivot table and write it to an Excel sheet.

    Args:
        df: Source DataFrame.
        writer: ExcelWriter object.
        sheet_name: Name of the pivot sheet.
        values: Column to aggregate.
        index: Row grouping column(s).
        columns: Column grouping column(s).
        aggfunc: Aggregation function ('sum', 'mean', 'count', etc.).

    Returns:
        The pivot table DataFrame.
    """
    pivot_df = pd.pivot_table(
        df,
        values=values,
        index=index,
        columns=columns,
        aggfunc=aggfunc,
        margins=True,
        margins_name="Total",
    )

    # Round numeric values
    pivot_df = pivot_df.round(2)

    pivot_df.to_excel(writer, sheet_name=sheet_name)

    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    # Auto-adjust column widths for pivot
    for idx in range(len(pivot_df.columns) + 1):
        worksheet.set_column(idx, idx, 15)

    return pivot_df


def create_excel_with_pivot(
    output_path: Union[str, Path],
    df: Optional[pd.DataFrame] = None,
    data_sheet_name: str = "Data",
    pivot_sheet_name: str = "Pivot",
    pivot_values: str = "Revenue",
    pivot_index: Union[str, List[str]] = "Category",
    pivot_columns: Optional[Union[str, List[str]]] = "Region",
    pivot_aggfunc: str = "sum",
    use_sample_data: bool = False,
    sample_rows: int = 100,
) -> Path:
    """Create an Excel file with a data sheet and a pivot table sheet.

    Args:
        output_path: Path for the output Excel file.
        df: DataFrame to use. If None and use_sample_data is True, generates sample data.
        data_sheet_name: Name of the data sheet.
        pivot_sheet_name: Name of the pivot table sheet.
        pivot_values: Column to aggregate in pivot.
        pivot_index: Row grouping for pivot.
        pivot_columns: Column grouping for pivot.
        pivot_aggfunc: Aggregation function for pivot.
        use_sample_data: Generate sample data if df is None.
        sample_rows: Number of rows for sample data.

    Returns:
        Path to the created Excel file.
    """
    output_path = Path(output_path)

    if df is None:
        if use_sample_data:
            df = generate_sample_data(rows=sample_rows)
        else:
            raise ValueError("Either provide a DataFrame or set use_sample_data=True")

    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        # Create data sheet
        create_data_sheet(df, writer, sheet_name=data_sheet_name)

        # Create pivot table sheet
        create_pivot_table(
            df,
            writer,
            sheet_name=pivot_sheet_name,
            values=pivot_values,
            index=pivot_index,
            columns=pivot_columns,
            aggfunc=pivot_aggfunc,
        )

    return output_path


def read_excel_to_dataframe(
    file_path: Union[str, Path],
    sheet_name: Optional[str] = None,
) -> pd.DataFrame:
    """Read an Excel file into a DataFrame.

    Args:
        file_path: Path to the Excel file.
        sheet_name: Specific sheet to read. If None, reads first sheet.

    Returns:
        DataFrame with the Excel data.
    """
    return pd.read_excel(file_path, sheet_name=sheet_name)


def create_chart(
    df: pd.DataFrame,
    output_path: Union[str, Path],
    chart_type: str = "bar",
    x_axis: str = "Category",
    y_axis: str = "Revenue",
    aggfunc: str = "sum",
    group_by: Optional[str] = None,
    title: Optional[str] = None,
    figsize: tuple = (10, 6),
) -> Path:
    """Create a chart from DataFrame and save as image.

    Args:
        df: Source DataFrame.
        output_path: Path for the output image (PNG).
        chart_type: Type of chart ('bar', 'line', 'pie', 'doughnut', 'scatter', 'area').
        x_axis: Column for X-axis (categories).
        y_axis: Column for Y-axis (values to aggregate).
        aggfunc: Aggregation function ('sum', 'mean', 'count', 'min', 'max').
        group_by: Optional column to group by (creates multiple series).
        title: Chart title. If None, auto-generated.
        figsize: Figure size as (width, height) tuple.

    Returns:
        Path to the created image file.
    """
    output_path = Path(output_path)

    # Ensure y_axis is numeric
    df = df.copy()
    if y_axis in df.columns:
        df[y_axis] = pd.to_numeric(df[y_axis], errors='coerce')

    # Aggregate data
    if group_by and group_by in df.columns:
        aggregated = df.groupby([x_axis, group_by])[y_axis].agg(aggfunc).unstack(fill_value=0)
    else:
        aggregated = df.groupby(x_axis)[y_axis].agg(aggfunc)

    # Create figure with style
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=figsize)

    if chart_type == 'bar':
        if isinstance(aggregated, pd.DataFrame):
            aggregated.plot(kind='bar', ax=ax, color=CHART_COLORS[:len(aggregated.columns)], edgecolor='white')
        else:
            aggregated.plot(kind='bar', ax=ax, color=CHART_COLORS[0], edgecolor='white')
    elif chart_type == 'line':
        if isinstance(aggregated, pd.DataFrame):
            aggregated.plot(kind='line', ax=ax, marker='o', linewidth=2, markersize=8, color=CHART_COLORS[:len(aggregated.columns)])
        else:
            aggregated.plot(kind='line', ax=ax, marker='o', linewidth=2, markersize=8, color=CHART_COLORS[0])
    elif chart_type in ['pie', 'doughnut']:
        if isinstance(aggregated, pd.DataFrame):
            data_to_plot = aggregated.sum(axis=1)
        else:
            data_to_plot = aggregated
        wedges, texts, autotexts = ax.pie(data_to_plot, labels=data_to_plot.index,
                                           colors=CHART_COLORS[:len(data_to_plot)],
                                           autopct='%1.1f%%', startangle=90)
        ax.set_ylabel('')
        for autotext in autotexts:
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')
    elif chart_type == 'scatter':
        if isinstance(aggregated, pd.DataFrame):
            for i, col in enumerate(aggregated.columns):
                ax.scatter(range(len(aggregated)), aggregated[col], label=col,
                          color=CHART_COLORS[i % len(CHART_COLORS)], s=100, alpha=0.7)
            ax.legend()
        else:
            ax.scatter(range(len(aggregated)), aggregated.values, color=CHART_COLORS[0], s=100, alpha=0.7)
        ax.set_xticks(range(len(aggregated)))
        ax.set_xticklabels(aggregated.index, rotation=45, ha='right')
    elif chart_type == 'area':
        if isinstance(aggregated, pd.DataFrame):
            aggregated.plot(kind='area', ax=ax, alpha=0.7, color=CHART_COLORS[:len(aggregated.columns)])
        else:
            aggregated.plot(kind='area', ax=ax, alpha=0.7, color=CHART_COLORS[0])

    # Set title
    if title is None:
        title = f"{aggfunc.title()} of {y_axis} by {x_axis}"
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel(x_axis, fontsize=11)
    if chart_type not in ['pie', 'doughnut']:
        ax.set_ylabel(y_axis, fontsize=11)
        ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()

    # Save figure
    plt.savefig(output_path, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)

    return output_path


def create_excel_with_charts(
    output_path: Union[str, Path],
    df: Optional[pd.DataFrame] = None,
    data_sheet_name: str = "Data",
    pivot_sheet_name: str = "Pivot",
    pivot_values: str = "Revenue",
    pivot_index: Union[str, List[str]] = "Category",
    pivot_columns: Optional[Union[str, List[str]]] = "Region",
    pivot_aggfunc: str = "sum",
    charts: Optional[List[Dict[str, Any]]] = None,
    use_sample_data: bool = False,
    sample_rows: int = 100,
) -> Path:
    """Create an Excel file with data, pivot table, and charts.

    Args:
        output_path: Path for the output Excel file.
        df: DataFrame to use. If None and use_sample_data is True, generates sample data.
        data_sheet_name: Name of the data sheet.
        pivot_sheet_name: Name of the pivot table sheet.
        pivot_values: Column to aggregate in pivot.
        pivot_index: Row grouping for pivot.
        pivot_columns: Column grouping for pivot.
        pivot_aggfunc: Aggregation function for pivot.
        charts: List of chart configurations, each a dict with keys:
                'chart_type', 'x_axis', 'y_axis', 'aggfunc', 'group_by' (optional)
        use_sample_data: Generate sample data if df is None.
        sample_rows: Number of rows for sample data.

    Returns:
        Path to the created Excel file.
    """
    output_path = Path(output_path)

    if df is None:
        if use_sample_data:
            df = generate_sample_data(rows=sample_rows)
        else:
            raise ValueError("Either provide a DataFrame or set use_sample_data=True")

    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        workbook = writer.book

        # Create formatted data sheet
        df.to_excel(writer, sheet_name=data_sheet_name, index=False, startrow=0, header=False)
        data_worksheet = writer.sheets[data_sheet_name]
        _format_excel_sheet(workbook, data_worksheet, df, 'data')

        # Create formatted pivot table sheet
        pivot_df = pd.pivot_table(
            df,
            values=pivot_values,
            index=pivot_index,
            columns=pivot_columns,
            aggfunc=pivot_aggfunc,
            margins=True,
            margins_name="Total",
        ).round(2)

        pivot_reset = pivot_df.reset_index()
        pivot_reset.columns = [str(c) for c in pivot_reset.columns]
        pivot_reset.to_excel(writer, sheet_name=pivot_sheet_name, index=False, startrow=0, header=False)
        pivot_worksheet = writer.sheets[pivot_sheet_name]
        _format_excel_sheet(workbook, pivot_worksheet, pivot_reset, 'pivot')

        # Create charts sheet if charts are specified
        if charts:
            chart_worksheet = workbook.add_worksheet('Charts')
            title_format = workbook.add_format({
                'bold': True,
                'font_size': 14,
                'font_color': '#217346'
            })

            row_offset = 0

            for i, chart_config in enumerate(charts):
                # Generate chart image
                chart_df = df.copy()
                y_axis = chart_config.get('y_axis', pivot_values)
                x_axis = chart_config.get('x_axis', pivot_index if isinstance(pivot_index, str) else pivot_index[0])
                chart_type = chart_config.get('chart_type', 'bar')
                aggfunc = chart_config.get('aggfunc', pivot_aggfunc)
                group_by = chart_config.get('group_by')

                if y_axis in chart_df.columns:
                    chart_df[y_axis] = pd.to_numeric(chart_df[y_axis], errors='coerce')

                if group_by and group_by in chart_df.columns:
                    aggregated = chart_df.groupby([x_axis, group_by])[y_axis].agg(aggfunc).unstack(fill_value=0)
                else:
                    aggregated = chart_df.groupby(x_axis)[y_axis].agg(aggfunc)

                # Create matplotlib figure
                plt.style.use('seaborn-v0_8-whitegrid')
                fig, ax = plt.subplots(figsize=(10, 6))

                if chart_type == 'bar':
                    if isinstance(aggregated, pd.DataFrame):
                        aggregated.plot(kind='bar', ax=ax, color=CHART_COLORS[:len(aggregated.columns)], edgecolor='white')
                    else:
                        aggregated.plot(kind='bar', ax=ax, color=CHART_COLORS[0], edgecolor='white')
                elif chart_type == 'line':
                    if isinstance(aggregated, pd.DataFrame):
                        aggregated.plot(kind='line', ax=ax, marker='o', linewidth=2, markersize=8, color=CHART_COLORS[:len(aggregated.columns)])
                    else:
                        aggregated.plot(kind='line', ax=ax, marker='o', linewidth=2, markersize=8, color=CHART_COLORS[0])
                elif chart_type in ['pie', 'doughnut']:
                    if isinstance(aggregated, pd.DataFrame):
                        data_to_plot = aggregated.sum(axis=1)
                    else:
                        data_to_plot = aggregated
                    ax.pie(data_to_plot, labels=data_to_plot.index, colors=CHART_COLORS[:len(data_to_plot)], autopct='%1.1f%%', startangle=90)
                    ax.set_ylabel('')
                elif chart_type == 'scatter':
                    if isinstance(aggregated, pd.DataFrame):
                        for j, col in enumerate(aggregated.columns):
                            ax.scatter(range(len(aggregated)), aggregated[col], label=col, color=CHART_COLORS[j % len(CHART_COLORS)], s=100, alpha=0.7)
                        ax.legend()
                    else:
                        ax.scatter(range(len(aggregated)), aggregated.values, color=CHART_COLORS[0], s=100, alpha=0.7)
                    ax.set_xticks(range(len(aggregated)))
                    ax.set_xticklabels(aggregated.index, rotation=45, ha='right')
                elif chart_type == 'area':
                    if isinstance(aggregated, pd.DataFrame):
                        aggregated.plot(kind='area', ax=ax, alpha=0.7, color=CHART_COLORS[:len(aggregated.columns)])
                    else:
                        aggregated.plot(kind='area', ax=ax, alpha=0.7, color=CHART_COLORS[0])

                ax.set_title(f"{aggfunc.title()} of {y_axis} by {x_axis}", fontsize=14, fontweight='bold', pad=20)
                ax.set_xlabel(x_axis, fontsize=11)
                if chart_type not in ['pie', 'doughnut']:
                    ax.set_ylabel(y_axis, fontsize=11)
                    ax.tick_params(axis='x', rotation=45)

                plt.tight_layout()

                # Save chart to bytes
                img_buf = io.BytesIO()
                plt.savefig(img_buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
                plt.close(fig)
                img_buf.seek(0)

                # Write chart title
                chart_worksheet.write(row_offset, 0, f"Chart {i+1}: {chart_type.title()} - {y_axis} by {x_axis}", title_format)

                # Insert image
                chart_worksheet.insert_image(row_offset + 1, 0, f'chart_{i}.png', {'image_data': img_buf})

                row_offset += 28

    return output_path


def _format_excel_sheet(workbook, worksheet, df, sheet_type='data'):
    """Apply professional formatting to an Excel sheet."""
    # Define formats
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#217346',
        'font_color': 'white',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': True
    })

    cell_format = workbook.add_format({
        'border': 1,
        'valign': 'vcenter'
    })

    number_format = workbook.add_format({
        'border': 1,
        'valign': 'vcenter',
        'num_format': '#,##0.00'
    })

    int_format = workbook.add_format({
        'border': 1,
        'valign': 'vcenter',
        'num_format': '#,##0'
    })

    total_format = workbook.add_format({
        'bold': True,
        'bg_color': '#D9EAD3',
        'border': 1,
        'valign': 'vcenter',
        'num_format': '#,##0.00'
    })

    total_label_format = workbook.add_format({
        'bold': True,
        'bg_color': '#D9EAD3',
        'border': 1,
        'valign': 'vcenter'
    })

    # Set row height for header
    worksheet.set_row(0, 25)

    # Auto-adjust column widths and apply header format
    for idx, col in enumerate(df.columns):
        max_length = max(
            df[col].astype(str).map(len).max() if len(df) > 0 else 0,
            len(str(col))
        ) + 3
        worksheet.set_column(idx, idx, min(max_length, 50))
        worksheet.write(0, idx, str(col), header_format)

    # Write data with appropriate formats
    for row_idx, row in enumerate(df.values):
        is_total_row = sheet_type == 'pivot' and row_idx == len(df) - 1

        for col_idx, value in enumerate(row):
            cell_row = row_idx + 1

            if is_total_row:
                fmt = total_label_format if col_idx == 0 else total_format
            elif isinstance(value, (int, float)) and not pd.isna(value):
                fmt = number_format if isinstance(value, float) and not value.is_integer() else int_format
            else:
                fmt = cell_format

            if pd.isna(value):
                worksheet.write(cell_row, col_idx, '', fmt)
            else:
                worksheet.write(cell_row, col_idx, value, fmt)

    # Freeze top row
    worksheet.freeze_panes(1, 0)

    # Add autofilter for data sheets
    if sheet_type == 'data' and len(df) > 0:
        worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
