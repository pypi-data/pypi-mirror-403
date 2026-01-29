#-----------------------------------------------------------------
#
#  Name:    core.py
#
#  Purpose: These are the essential functions for DataNova / DSTK
#
#  Date:    Winter 2025
#
#  Author:  Riley & Justyna
#
#-----------------------------------------------------------------
#                            NOTES
#
#  
# This line always has to be first!!!!
from __future__ import annotations


# Standard Library 
import os
import textwrap
from typing import Optional, Sequence, Union

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.figure import Figure
import matplotlib.ticker as mtick


import pandas as pd 
import numpy as np


import statsmodels.api as sm



def hello():
    print("Welcome to DataNova!")


#pd.set_option('display.max_columns', None)

#---------------------------------------------
#       Utility Functions for Plotting    


def _set_plot_style() -> None:
    """Consistent, professional style (matches our STIX look)."""
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["STIXGeneral"],
            "mathtext.fontset": "stix",
        }
    )

def _style_grid(ax, *, axis: str = "x") -> None:
    """Light dashed grid behind bars."""
    ax.grid(
        axis=axis,
        linestyle=(0, (5, 10)),
        linewidth=0.8,
        color="#c7c7c7",
        alpha=0.7,
        zorder=1.0,
    )


def _wrap_cell_text(x: object, width: int = 12) -> str:
    """Wrap long strings to multiple lines for narrow tables."""
    
    s = "" if x is None else str(x)
    return "\n".join(textwrap.wrap(s, width=width)) if s else s


def _set_table_column_widths(table, widths):
    """
    widths: list of floats, one per column, in *axes fraction* units.
    """
    cells = table.get_celld()
    nrows = max(r for (r, c) in cells.keys()) + 1

    for c, w in enumerate(widths):
        for r in range(nrows):
            if (r, c) in cells:
                cells[(r, c)].set_width(w)



#----------------------------------------
#       Descriptive Plotting     


def bar_chart_data( df              : pd.DataFrame, 
                    var_name        : str, 
                    *,
                    top_n_rows      : int = 5 , 
                    label_max_chars : int = 35  ) -> pd.DataFrame:
    """
    Generate bar chart data with: counts & cumulative probability.
    
    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.

    var_name : str
        Column name to analyze (data must be categorical / text).

    Returns
    -------
    pd.DataFrame
        A DataFrame with most common values.
    """

    col = df[var_name].fillna("N/A").astype(str)

    pivot_table = (
        col.value_counts()
           .reset_index()
           .rename(columns={"index": var_name})
    )

    # ---- Truncate labels safely
    pivot_table[var_name] = pivot_table[var_name].where(
        pivot_table[var_name].str.len() <= label_max_chars,
        pivot_table[var_name].str.slice(0, label_max_chars - 2) + " ..."
    )

    pivot_table["%"] = (
        pivot_table["count"] / pivot_table["count"].sum() * 100
    ).round(2)

    pivot_table["Cum. %"] = pivot_table["%"].cumsum().round(2)

    return( pivot_table.head(top_n_rows) )



def bar(
    df: pd.DataFrame,
    col_name: str,
    *,
    top_n: int = 5,
    bar_color: str = "#118dff",
    width: float = 10.0,
    height: float = 5.0,
    table_wrap_width: int = 12,
    ) -> Figure:
    """
    Creates a combined plot with:
    - A bar chart on the left
    - A summary table of most frequent values on the right

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.

    col_name : str
        Column name to plot (data must be text).

    top_n : int
        Number of bars

    bar_color : str
        Bar color as HEX code (e.g., '#4d9b1e').

    width : float, default 10.0
        Figure width in inches.

    height : float, default 5.0
        Figure height in inches.
    
    table_wrap_width: int, default 12
        Maximum number of characters per line for text wrapping inside the table categorical column.

    Returns
    -------
    matplotlib.figure.Figure
        Final graph created
    """

    _set_plot_style()

    # ---- Data
    bar_data = bar_chart_data(df, col_name, top_n_rows=top_n).copy()

    # Wrap the categorical column in the TABLE (not the y-axis labels)
    bar_data[col_name] = bar_data[col_name].apply(lambda s: _wrap_cell_text(s, width=table_wrap_width))

    # ---- Layout
    fig = plt.figure(figsize=(width, height)  ,  constrained_layout=True)

    gs = fig.add_gridspec(1, 2, width_ratios=[1.15, 0.80], wspace=0.04)

    # ---- Bar chart
    ax_bar = fig.add_subplot(gs[0, 0])
    ax_bar.barh(
        bar_data[col_name],
        bar_data["count"],
        color=bar_color,
        edgecolor="black",
        zorder=2.0)

    ax_bar.set_title(f"Bar Chart of {col_name}", fontsize=15)
    ax_bar.set_xlabel("Occurrences", fontsize=14)
    ax_bar.set_ylabel(col_name, fontsize=14)

    for label in (ax_bar.get_xticklabels() + ax_bar.get_yticklabels()):
        label.set_fontsize(11)
    
    ax_bar.invert_yaxis()
    ax_bar.spines[["top", "right"]].set_visible(False)

    _style_grid(ax_bar, axis="x")
    ax_bar.xaxis.set_major_formatter(mtick.StrMethodFormatter("{x:,.0f}"))

    # ---- Table
    ax_table = fig.add_subplot(gs[0, 1])
    ax_table.axis("off")



    # Format BEFORE creating the table
    table_df = bar_data.copy()
    table_df["count"] = pd.to_numeric(table_df["count"], errors="coerce").fillna(0).astype(int).map("{:,}".format)
    table_df["%"] = pd.to_numeric(table_df["%"], errors="coerce").map(lambda v: f"{v:.2f}")
    table_df["Cum. %"] = pd.to_numeric(table_df["Cum. %"], errors="coerce").map(lambda v: f"{v:.2f}")



    table = ax_table.table(
        cellText=table_df.values,
        colLabels=table_df.columns,
        loc="center",
        cellLoc="center",
        bbox=[0.00 , 0.00 , 0.95 , 0.95 ]  # BBox ( left position , bottom position , table width (%), table height (%) )
    )

    table.auto_set_font_size(False)
    table.set_fontsize(11)            # slightly smaller = cleaner


    # Base styling first
    for cell in table.get_celld().values():
        cell.set_linewidth(0.4)
        cell.PAD = 0.12
        cell.get_text().set_multialignment("center")

    # Set column widths (must happen after table exists)
    _set_table_column_widths(table, widths=[0.45, 0.20, 0.17, 0.18])

    cells = table.get_celld()

    # Header styling (do this AFTER base styling so it doesn't get overwritten)
    ncols = len(table_df.columns)
    for c in range(ncols):
        cells[(0, c)].get_text().set_weight("bold")
        cells[(0, c)].set_facecolor("#ebebeb")
        cells[(0, c)].PAD = 0.22


    # Left align the first column excluding the header. That's why we have "+1"
    nrows = max(r for (r, c) in cells.keys()) + 1
    for r in range(1, nrows):
        cells[(r, 0)].get_text().set_ha("center")
        cells[(r, 0)].PAD = 0.05


    # Do not show plot IF DataNova is running in Jupyter. 
    # This prevents double plotting. 
    backend = matplotlib.get_backend().lower()
    if "matplotlib_inline" in backend:        
        plt.close(fig)
    

    return( fig )



def hist_data(df : pd.DataFrame,  var_name : str) -> pd.DataFrame:
    """
    Calculate statistics for a numeric column in a pandas DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.

    var_name : str
        Column name to analyze (data must be numeric).

    Returns
    -------
    pd.DataFrame
        A DataFrame with statistic names and their values.
    """
        
    if var_name not in df.columns:
        raise ValueError(f"Column '{var_name}' does not exist in the DataFrame.")

    column_data = df[var_name]
    non_blank_data = column_data.dropna()

    stats = {
        "Statistic": [
            "Min", "25% Quartile","Mean", "Median",  "75% Quartile", 
            "Max",  "Standard Deviation", 
            "Count of Rows", "% Blank"
        ],
        "Value": [
            column_data.min().round(2),
            column_data.quantile(0.25).round(2),
            column_data.mean().round(2),
            column_data.median().round(2),
            column_data.quantile(0.75).round(2),
            column_data.max().round(2),
            column_data.std().round(2),
            int(len(column_data)),
            round(100 * (1 - len(non_blank_data) / len(column_data)), 2) if len(column_data) > 0 else 0
        ]
    }

    S = pd.DataFrame(stats) 

    # --- formatting rules ---
    def format_value(row):
        stat = row["Statistic"]
        val = row["Value"]

        if stat == "Count of Rows":
            return f"{int(val):,}"          # 1,752
        elif stat == "% Blank":
            return f"{val:.2f}"             # 5.02
        else:
            return f"{val:.2f}"             # floats

    S["Value"] = S.apply(format_value, axis=1)

    return( S )


def hist(               df       : pd.DataFrame, 
                        col_name : str, 
                        *,
                        xlim: Union[list, None] = None ,
                        n_bins: int = 20 ,
                        bar_color: str = "#118dff" ,
                        width: float = 10.0 ,
                        height: float = 5.0 ,   
                        ) -> Figure:
    """
    Create a combined visualization: box plot, histogram, and a summary-statistics table.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.

    col_name : str
        Column name to plot (data must be numeric).
    
    xlim: list
        The min and max range to be plotted

    bar_color : str
        Bar/box color (e.g., '#4d9b1e').

    n_bins : int, default 20
        Number of histogram bins.

    width : float, default 13.33
        Figure width in inches.

    height : float, default 6.0
        Figure height in inches.

    Returns
    -------
    matplotlib.figure.Figure
        Final graph created
    """
    
    _set_plot_style()

    # Calculate statistics for the table
    stats = hist_data(df, col_name)  # Use your utility function here 
    stats.columns = ["Statistic", "Value"]  # Ensure proper column labels 

    data = df[col_name].dropna()    

    # Create the figure 
    fig = plt.figure(figsize=(width, height)  ,  constrained_layout=True)
    gs = fig.add_gridspec(2, 3, width_ratios=[1.3, 1.3, 1.4], height_ratios=[1, 3] , wspace=0.04)

    # Box Plot (Top-Left)
    ax_box = fig.add_subplot(gs[0, 0:2])
    ax_box.boxplot(data, vert=False, patch_artist=True, boxprops=dict(facecolor=bar_color), zorder=2.0)  
    ax_box.tick_params(axis="x",which="both",bottom=False,top=False,labelbottom=False)

    if xlim is not None:
        ax_box.set_xlim(xlim)
        
    ax_box.axes.get_yaxis().set_visible(False)                              # Hide y-axis for box plot
    ax_box.set_xticklabels([])                                              # Remove x-axis labels
    ax_box.spines[['top','left', 'right', 'bottom']].set_visible(False)     # Remove border
    ax_box.set_title(f"Histogram of {col_name}", fontsize = 15)             # Set title
    
    
    #--------------------
    # Histogram (Bottom-Left)
    ax_hist = fig.add_subplot(gs[1, 0:2])

    _style_grid(ax_hist, axis="x")
    _style_grid(ax_hist, axis="y")


    if xlim == None:
        ax_hist.hist(data, bins=n_bins, color=bar_color, edgecolor='black', zorder = 4.0)
    else:
        ax_hist.hist(data, bins=n_bins, range = xlim, color=bar_color, edgecolor='black', zorder = 4.0)
    
    ax_hist.set_xlabel(col_name, fontsize=14)
    ax_hist.set_ylabel("Count", fontsize = 14)

    # Increase font size
    for label in (ax_hist.get_xticklabels() + ax_hist.get_yticklabels()): 
        label.set_fontsize(11)
    
    ax_hist.spines[['top','right']].set_visible(False)
    
    # commas for y-axis (12345 --> 12,345)
    ax_hist.yaxis.set_major_formatter(
        mtick.StrMethodFormatter('{x:,.0f}')
    )


    #--------------------
    #   Table (Right)
    ax_table = fig.add_subplot(gs[:, 2])  # Span rows 0 and 1 for the table
    ax_table.axis("off")  # Turn off the axis


    table = ax_table.table(
        cellText=stats.values,
        colLabels=stats.columns,
        loc="center",
        cellLoc="center",
        bbox=[0.00 , 0.00 , 0.95 , 0.80 ] # BBox ( left position , bottom position , table width (%), table height (%) )
        )
    
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.auto_set_column_width(col=list(range(len(stats.columns))))


    cells = table.get_celld()

    # Slightly lighten table borders
    for cell in table.get_celld().values():
        cell.set_linewidth(0.5)

    ncols = len(stats.columns)
    for c in range(ncols):
        cells[(0, c)].get_text().set_weight("bold")
        cells[(0, c)].set_facecolor("#ebebeb")
        cells[(0, c)].PAD = 0.22
    
    # Do not show plot IF DataNova is running in Jupyter. 
    # This prevents double plotting. 
    backend = matplotlib.get_backend().lower()
    if "matplotlib_inline" in backend:        
        plt.close(fig)

    return( fig )




#----------------------------------------
#   Exploritory Data Analysis - EDA   


def _in_notebook() -> bool:
    """
    This function returns True or False:
    
    True  --> The Python code is       being executed in a Jupyter Notebook
    False --> The Python code is  NOT  being executed in a Jupyter Notebook
    
    Returns
    ----------
    bool
    """
    try:
        from IPython import get_ipython
        shell = get_ipython().__class__.__name__
        return shell == "ZMQInteractiveShell"  # Jupyter/VSCode notebooks
    except Exception:
        return False
    

def eda( df: pd.DataFrame ) -> list[Figure]:
    """
    This function is a quick “EDA” analysis. (Exploratory Data Analysis)
    Plot the distribution for every column in a dataset.  

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.

    Returns
    ----------
    list[matplotlib.figure.Figure]
        Figures created.
    """

    n_row, n_col = df.shape
    bar_colors = ["#826fc2","#143499","#4d9b1e","#f865c6","#ecd378","#ba004c","#8f4400","#f65656"]*(n_col*2)
    figs = []


    in_nb = _in_notebook()
    if in_nb:
        from IPython.display import display
    
        
    for count, var_name in enumerate(df.columns):
        
        # IF the column is 100% blank then skip it
        if df[var_name].isna().all():
            continue


        bar_color_i = bar_colors[count]            

        if pd.api.types.is_numeric_dtype( df[var_name] ):
            fig = hist(df,var_name, bar_color = bar_color_i)
            figs.append(fig)

        elif (pd.api.types.is_string_dtype(df[var_name]) or pd.api.types.is_object_dtype(df[var_name]) or pd.api.types.is_categorical_dtype(df[var_name])):
            fig = bar(df, var_name, bar_color = bar_color_i)
            figs.append(fig)
        

        # IF the data type is not numeric, or text, 
        # THEN stop the loop 
        # AND go to the next iteration
        else: 
            continue
        
        if in_nb:
            display(fig)

    return(figs)



#----------------------------------------
#       Regression Modeling    

#### KEEP THIS ONE!!!!




from typing import Optional, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm


def lm(
    df: pd.DataFrame,
    xvar: str,
    yvar: str,
    *,
    xtitle: Optional[str] = None,
    ytitle: Optional[str] = None,
    xlimit: Union[list, None] = None,
    ylimit: Union[list, None] = None,
    alpha: float = 0.8,
    show_summary: bool = True):
    """
    PURPOSE
    -------
    Fit a simple linear regression model using statsmodels and visualize the results.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.

    xvar : str
        Independent variable (X).

    yvar : str
        Dependent variable (Y).

    xtitle, ytitle : str, optional
        Axis labels. Defaults to column names.
    
    xlimit: list
        The min and max range to be plotted (x axis)
    
    ylimit: list
        The min and max range to be plotted (y axis)

    alpha : float, optional
        Scatter transparency (default = 0.8).

    show_summary : bool, optional
        Whether to print the regression summary table (default = True).

    Returns
    -------
    model : statsmodels.regression.linear_model.RegressionResultsWrapper
        The fitted statsmodels OLS regression model.
    """

    if xvar not in df.columns or yvar not in df.columns:
        raise ValueError("xvar/yvar must be valid column names in df.")

    data = df[[xvar, yvar]].dropna()

    if data.empty:
        raise ValueError("No data remaining after dropping NA for xvar and yvar.")

    X = sm.add_constant(data[xvar])
    y = data[yvar]
    model = sm.OLS(y, X).fit()

    if show_summary:
        print(model.summary())

    # Use xlimit for line extent if provided
    if xlimit is not None:
        if len(xlimit) != 2:
            raise ValueError("xlimit must be a (min, max) pair.")
        x_min, x_max = xlimit
    else:
        x_min, x_max = float(data[xvar].min()), float(data[xvar].max())

    x_vals = np.linspace(x_min, x_max, 200)
    X_pred = sm.add_constant(x_vals)
    y_pred = model.predict(X_pred)

    x_axis_title = xvar if xtitle is None else xtitle
    y_axis_title = yvar if ytitle is None else ytitle


    #----------------
    #      Plot
    _set_plot_style()
    
    fig, ax = plt.subplots(figsize=(5.5, 4.8))

    _style_grid(ax, axis="x")
    _style_grid(ax, axis="y")

    
    ax.scatter(data[xvar], data[yvar], alpha=alpha, zorder=2)

    
    slope = model.params[xvar]
    intercept = model.params["const"]
    r2 = model.rsquared
    eqn = f"Y = {slope:.3f}·X + {intercept:.2f} (R²={r2:.2f})"

    
    ax.plot(x_vals, y_pred, color="red", linewidth=2, label=eqn, zorder=3)

    
    if xlimit is not None:
        ax.set_xlim(xlimit)
    if ylimit is not None:
        ax.set_ylim(ylimit)

    
    ax.set_xlabel(x_axis_title, fontsize=16)
    ax.set_ylabel(y_axis_title, fontsize=16)
    ax.tick_params(labelsize=13)

    
    ax.spines[["top", "right"]].set_visible(False)

    
    ax.legend( loc="upper left", bbox_to_anchor=(.15, 1.25), fancybox=True, shadow=True, frameon=True, fontsize=12)

    fig.tight_layout()
    
    # Do not show plot IF DataNova is running in Jupyter. 
    # This prevents double plotting. 
    backend = matplotlib.get_backend().lower()
    if "matplotlib_inline" in backend:        
        plt.close(fig)
    
    return( fig , model )



#----------------------------------------
#       Data Loading & Profile    


def load_data(uploaded_file:str,  excel_sheet: Optional[Union[str, int]] = 0) -> pd.DataFrame:
    """
    PURPOSE: Load an Excel, CSV, or Parquet file into a Pandas DataFrame.

    Returns
    -------
    pd.DataFrame
        The loaded data.
    """

    uploaded_file = str(uploaded_file)
    _, file_extension = os.path.splitext(uploaded_file)
    file_extension = file_extension.lower()


    if file_extension in [".xlsx", ".xls"]:
        df = pd.read_excel(uploaded_file, sheet_name= excel_sheet, engine=None)
        return(df)
        
    elif file_extension == ".csv":
        df = pd.read_csv(uploaded_file, engine="c", low_memory=False)
        return(df)
        
    elif file_extension == ".parquet":
        df = pd.read_parquet( uploaded_file, engine = 'auto' )
        return(df)
        
    else:
        raise ValueError(f"Unsupported file extension: '{file_extension}'")
    

def profile( df:pd.DataFrame ) -> pd.DataFrame:
    """
    PURPOSE
    -------
    Create a data profile of a pandas DataFrame to assess data quality.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.

    Returns
    -------
    pd.DataFrame
        A summary with numeric stats, column metadata, etx.
    """

    n_row, n_col = df.shape
    r_total = "{:,}".format(n_row)
    print("ROW TOTAL = " + str(r_total) + " COLUMNS = " + str(n_col))

    # Basic summary
    summary = pd.DataFrame({
        "Variable Name": df.columns,
        "Variable Type": df.dtypes.astype(str),
        "Missing Count": df.isna().sum(),
        "% Blank": (df.isna().mean() * 100).round(0).astype("Int64"),
        "Unique Values": df.nunique(dropna=True),
        "Most Frequent Value": df.apply(
            lambda col: col.mode(dropna=True).iloc[0] if not col.mode(dropna=True).empty else pd.NA
        ),
    })

    # Universal describe (works for text-only, numeric-only, or mixed)
    desc = (
        df.describe(include="all")
          .T
          .reset_index()
          .rename(columns={"index":"Variable Name", 'count':'Count', 'unique':'Unique', 'top':'Top', "mean":"Mean", "50%": "Median", "max":"Max", "min":"Min", "std":"Standard Deviation"})
    )

    # Round numeric-looking stats if present (coerce non-numerics to NaN, which stay untouched)
    for col in ["Mean", "Standard Deviation", "Min", "25%", "Median", "75%", "Max"]:
        if col in desc.columns:
            desc[col] = pd.to_numeric(desc[col], errors="coerce").round(2)

    # Merge and return
    final = summary.merge(desc, on="Variable Name", how="left")


    if 'freq' in final.columns:
        final.drop(columns='freq', inplace=True)

    if 'top' in final.columns:
        final.drop(columns='top', inplace=True)

    if 'Top' in final.columns:
        final.drop(columns='Top', inplace=True)

    if 'Count' in final.columns:
        final.drop(columns='Count', inplace=True)

    if 'Unique' in final.columns:
        final.drop(columns='Unique', inplace=True)

    return( final )



#----------------------------------------
#       Appendix - Nice to Have  


def highlight_missing(val):
    """
    Color code cells in '%_Blank' based on thresholds (0-100 scale).

    95-100 %    : #b80000
    90- 95 %    : #c11e11
    85- 90 %    : #c62d19
    80- 85 %    : #ca3b21
    75- 80 %    : #cf4a2a
    70- 75 %    : #d35932
    65- 70 %    : #d8673a
    60- 65 %    : #dc7643
    55- 60 %    : #e0854b
    50- 55 %    : #e59353
    45- 50 %    : #e9a25b
    40- 45 %    : #eeb164
    35- 40 %    : #f2bf6c 
    30- 35 %    : #f7ce74
    25- 30 %    : #fbdd7c
    20- 25 %    : #ffeb84
    15- 20 %    : #d7df81
    10- 15 %    : #b0d47f
     5- 10 %    : #8ac97d
     0-  5 %    : #63be7b
    """

    if val > 95:
        color = '#b80000'
    elif val > 90:
        color = '#c11e11'
    elif val > 85:
        color = '#c62d19'
    elif val > 80:
        color = '#ca3b21'
    elif val > 75:
        color = '#cf4a2a'
    elif val > 70:
        color = '#d35932'
    elif val > 65:
        color = '#d8673a'
    elif val > 60:
        color = '#dc7643'
    elif val > 55:
        color = '#e0854b'
    elif val > 50:
        color = '#e59353'
    elif val > 45:
        color = '#e9a25b'
    elif val > 40:
        color = '#eeb164'
    elif val > 35:
        color = '#f2bf6c'
    elif val > 30:
        color = '#f7ce74'
    elif val > 25:
        color = '#fbdd7c'
    elif val > 20:
        color = '#ffeb84'
    elif val > 15:
        color = '#d7df81'
    elif val > 10:
        color = '#b0d47f'
    elif val > 5:
        color = '#8ac97d'
    else:
        color = '#63be7b'
    
    return f'background-color: {color}'

WINE_DF = pd.DataFrame({
    'country': ['US', 'Spain', 'US', 'US', 'France', 'Spain', 'Spain', 'Spain', 'US', 'US', 'Italy', 'US', 'US', 'France', 'US', 'US', 'US', 'Spain', 'France', 'US', 'US', 'Spain', 'Spain', 'US', 'US', 'New Zealand', 'US', 'US', 'US', 'US', 'Bulgaria', 'US', 'Italy', 'France', 'US', 'Italy', 'France', 'Italy', 'Italy', 'Italy', 'Spain', 'Spain', 'US', 'Italy', 'France', 'Italy', 'Italy', 'US', 'Italy', 'US', 'Italy', 'France', 'France', 'France', 'US', 'US', 'France', 'US', 'US', 'Italy', 'Argentina', 'Australia', 'Argentina', 'France', 'Portugal', 'US', 'France', 'US', 'US', 'US', 'US', 'US', 'Italy', 'US', 'Portugal', 'US', 'France', 'US', 'US', 'Italy', 'US', 'Israel', 'Italy', 'Italy', 'Italy', 'Italy', 'France', 'US', 'US', 'US', 'US', 'Portugal', 'Italy', 'US', 'Portugal', 'France', 'US', 'US', 'France', 'France', 'US', 'US', 'Italy', 'US', 'US', 'US', 'US', 'US', 'US', 'US', 'Portugal', 'Argentina', 'US', 'US', 'South Africa', 'Argentina', 'Spain', 'France', 'France', 'Portugal', 'US', 'US', 'US', 'US', 'US', 'US', 'US', 'US', 'Spain', 'Italy', 'Italy', 'US', 'US', 'US', 'US', 'US', 'US', 'US', 'Spain', 'France', 'France', 'US', 'US', 'US', 'US', 'US', 'US', 'Spain', 'US', 'US', 'US', 'Greece', 'Spain', 'Greece', 'Greece', 'Chile', 'France', 'US', 'Spain', 'Chile', 'US', 'US', 'Spain', 'US', 'US', 'US', 'Italy', 'Italy', 'Portugal', 'US', 'US', 'Chile', 'Greece', 'US', 'France', 'Spain', 'Italy', 'Italy', 'US', 'Chile', 'US', 'US', 'US', 'US', 'Argentina', 'US', 'US', 'US', 'Spain', 'Spain', 'Argentina', 'France', 'France', 'France', 'France', 'France', 'US', 'US', 'US', 'US', 'US', 'US', 'France', 'France', 'US', 'US', 'US', 'US', 'US', 'Spain', 'Portugal', 'Italy', 'US', 'Italy', 'France', 'France', 'Morocco', 'Italy', 'France', 'France', 'US', 'US', 'France', 'US', 'Italy', 'France', 'US', 'US', 'US', 'Portugal', 'US', 'US', 'US', 'US', 'Italy', 'France', 'France', 'France', 'Portugal', 'Italy', 'France', 'France', 'France', 'France', 'France', 'US', 'US', 'Romania', 'US', 'US', 'US', 'Italy', 'US', 'US', 'US', 'Italy', 'US', 'US', 'Italy', 'Spain', 'Spain', 'France', 'US', 'US', 'Italy', 'France', 'US', 'US', 'US', 'Argentina', 'France', 'France', 'US', 'US', 'US', 'US', 'Italy', 'Portugal', 'Portugal', 'US', 'Italy', 'Italy', 'France', 'France', 'US', 'US', 'France', 'France', 'France', 'US', 'France', 'Portugal', 'US', 'US', 'France', 'US', 'Italy', 'Italy', 'US', 'US', 'US', 'US', 'Italy', 'US', 'US', 'New Zealand', 'US', 'US', 'US', 'US', 'US', 'Italy', 'Italy', 'US', 'US', 'US', 'US', 'US', 'France', 'US', 'France', 'Spain', 'France', 'Spain', 'US', 'France', 'Argentina', 'France', 'France', 'US', 'Italy', 'Germany', 'US', 'Spain', 'US', 'Portugal', 'US', 'US', 'US', 'Italy', 'Italy', 'US', 'Italy', 'US', 'Portugal', 'Portugal', 'US', 'US', 'Germany', 'Italy', 'US', 'US', 'France', 'Portugal', 'US', 'Israel', 'US', 'US', 'Italy', 'Spain', 'US', 'US', 'US', 'France', 'France', 'US', 'Italy', 'Germany', 'France', 'France', 'France', 'US', 'US', 'France', 'Italy', 'Italy', 'US', 'Italy', 'Germany', 'US', 'US', 'US', 'US', 'Spain', 'Germany', 'Spain', 'US', 'US', 'US', 'US', 'US', 'US', 'Italy', 'US', 'Canada', 'Spain', 'France', 'Italy', 'Italy', 'Moldova', 'Italy', 'Italy', 'Italy', 'US', 'France', 'France', 'US', 'US', 'US', 'US', 'Spain', 'Hungary', 'Italy', 'US', 'US', 'US', 'US', 'Italy', 'Italy', 'Italy', 'US', 'US', 'US', 'US', 'Spain', 'Spain', 'US', 'France', 'US', 'US', 'US', 'US', 'Italy', 'Italy', 'France', 'US', 'US', 'US', 'Italy', 'Spain', 'Italy', 'US', 'Spain', 'Spain', 'Spain', 'US', 'Spain', 'Italy', 'Italy', 'Italy', 'Portugal', 'Italy', 'US', 'US', 'Portugal', 'Argentina', 'US', 'Portugal', 'US', 'US', 'Argentina', 'South Africa', 'US', 'US', 'US', 'US', 'France', 'Argentina', 'US', 'Argentina', 'US', 'Portugal', 'US', 'Portugal', 'US', 'US', 'France', 'US', 'Portugal', 'Portugal', 'US', 'Greece', 'France', 'Italy', 'France', 'France', 'Germany', 'Italy', 'US', 'US', 'Italy', 'France', 'US', 'US', 'US', 'Portugal', 'US', 'Italy', 'Italy', 'Spain', 'France', 'US', 'Chile', 'US', 'US', 'US', 'Spain', 'Italy', 'Spain', 'Spain', 'US', 'France', 'Portugal', 'US', 'US', 'US', 'US', 'Canada', 'US', 'Portugal', 'US', 'Portugal', 'US', 'US', 'US', 'France', 'France', 'US', 'US', 'Hungary', 'Italy', 'US', 'Italy', 'France', 'Portugal', 'France', 'US', 'Chile', 'US', 'US', 'US', 'US', 'Germany', 'France', 'France', 'US', 'US', 'Germany', 'US', 'Italy', 'France', 'France', 'France', 'France', 'France', 'US', 'Italy', 'US', 'Italy', 'Greece', 'US', 'US', 'Italy', 'US', 'Spain', 'Spain', 'US', 'Germany', 'US', 'US', 'US', 'US', 'France', 'US', 'US', 'US', 'Italy', 'France', 'US', 'US', 'France', 'US', 'Austria', 'US', 'US', 'US', 'Spain', 'Austria', 'Austria', 'US', 'US', 'US', 'US', 'US', 'US', 'Austria', 'US', 'US', 'Spain', 'France', 'US', 'US', 'US', 'Portugal', 'Italy', 'US', 'Germany', 'Germany', 'Germany', 'Germany', 'Germany', 'Italy', 'US', 'Portugal', 'US', 'France', 'US', 'US', 'US', 'Germany', 'Germany', 'Germany', 'Germany', 'Germany', 'Germany', 'US', 'Italy', 'France', 'Portugal', 'France', 'US', 'Australia', 'Italy', 'Portugal', 'Italy', 'US', 'US', 'Italy', 'Italy', 'Italy', 'Italy', 'Spain', 'US', 'France', 'Portugal', 'US', 'US', 'France', 'France', 'Germany', 'US', 'Italy', 'US', 'Italy', 'US', 'US', 'US', 'Italy', 'Italy', 'Italy', 'Australia', 'France', 'Argentina', 'France', 'US', 'US', 'France', 'US', 'France', 'Italy', 'US', 'US', 'France', 'US', 'US', 'US', 'Croatia', 'Italy', 'US', 'France', 'France', 'France', 'France', 'US', 'France', 'US', 'US', 'US', 'France', 'Spain', 'US', 'Spain', 'Bulgaria', 'US', 'US', 'US', 'US', 'US', 'US', 'Italy', 'US', 'Italy', 'US', 'US', 'US', 'Canada', 'US', 'US', 'US', 'US', 'US', 'Slovenia', 'US', 'Italy', 'Canada', 'US', 'Spain', 'Italy', 'US', 'France', 'US', 'South Africa', 'Argentina', 'Argentina', 'South Africa', 'US', 'France', 'France', 'US', 'France', 'Italy', 'Portugal', 'France', 'France', 'South Africa', 'US', 'US', 'Argentina', 'Italy', 'Argentina', 'Portugal', 'South Africa', 'Argentina', 'Spain', 'South Africa', 'France', 'Argentina', 'US', 'Bulgaria', 'Israel', 'France', 'Spain', 'US', 'US', 'US', 'France', 'US', 'Italy', 'US', 'Italy', 'Chile', 'US', 'US', 'US', 'Chile', 'Italy', 'Chile', 'US', 'US', 'Italy', 'Chile', 'US', 'US', 'US', 'Italy', 'Portugal', 'Portugal', 'Portugal', 'Chile', 'France', 'Italy', 'Italy', 'US', 'Italy', 'US', 'France', 'France', 'France', 'France', 'France', 'US', 'Italy', 'US', 'US', 'US', 'France', 'US', 'US', 'US', 'US', 'US', 'US', 'US', 'US', 'US', 'US', 'US', 'US', 'US', 'France', 'Italy', 'Greece', 'US', 'US', 'Italy', 'France', 'France', 'France', 'France', 'France', 'Italy', 'US', 'US', 'US', 'Italy', 'Australia', 'US', 'US', 'US', 'US', 'US', 'US', 'US', 'Chile', 'Spain', 'US', 'US', 'US', 'Germany', 'US', 'US', 'Spain', 'US', 'US', 'Spain', 'US', 'US', 'France', 'France', 'France', 'US', 'Canada', 'Bulgaria', 'France', 'France', 'US', 'Italy', 'France', 'Spain', 'Spain', 'Italy', 'US', 'Italy', 'Italy', 'Spain', 'Italy', 'Italy', 'Italy', 'Italy', 'US', 'US', 'US', 'US', 'Chile', 'Italy', 'France', 'Italy', 'Italy', 'US', 'US', 'Italy', 'Italy', 'Portugal', 'Portugal', 'France', 'US', 'US', 'US', 'US', 'US', 'US', 'US', 'Chile', 'US', 'US', 'US', 'US', 'Italy', 'Italy', 'France', 'Argentina', 'US', 'US', 'France', 'US', 'US', 'US', 'France', 'France', 'France', 'France', 'France', 'US', 'US', 'US', 'US', 'US', 'US', 'US', 'Spain', 'US', 'US', 'France', 'US', 'Spain', 'US', 'US', 'US', 'US', 'US', 'Italy', 'Portugal', 'Portugal', 'Portugal', 'France', 'US', 'Chile', 'France', 'Chile', 'US', 'Spain', 'US', 'Germany', 'Chile', 'Italy', 'US', 'Italy', 'US', 'Chile', 'Italy', 'Portugal', 'Italy', 'US', 'US', 'Italy', 'Italy', 'US', 'Portugal', 'US', 'Greece', 'Italy', 'US', 'Portugal', 'US', 'Spain', 'Italy', 'Israel', 'US', 'Germany', 'US', 'Israel', 'Italy', 'Portugal', 'US', 'Israel', 'US', 'US', 'Israel', 'Italy', 'US', 'Italy', 'Italy', 'Italy', 'Italy', 'Italy', 'Spain', 'Italy', 'Australia', 'US', 'US', 'Italy', 'US', 'Israel', 'Portugal', 'Portugal', 'Portugal', 'Portugal', 'France', 'France', 'Argentina', 'Portugal', 'US', 'US', 'Portugal', 'Portugal', 'Portugal', 'South Africa', 'Argentina', 'South Africa', 'France', 'US', 'South Africa', 'France', 'France', 'France', 'Portugal', 'Portugal', 'France', 'US', 'Italy', 'Germany', 'US', 'Italy', 'US', 'France', 'Portugal', 'Portugal', 'Portugal', 'US', 'US', 'Portugal', 'Portugal', 'Germany', 'Portugal', 'France', 'France', 'Germany', 'Chile', 'Chile', 'Italy', 'US', 'Chile', 'Italy', 'Portugal', 'US', 'Portugal', 'Portugal', 'Portugal', 'Portugal', 'US', 'Italy', 'Italy', 'US', 'US', 'US', 'US', 'US', 'Argentina', 'US', 'Argentina', 'Portugal', 'Bulgaria', 'US', 'Italy', 'Argentina', 'Spain', 'Australia', 'US', 'Croatia', 'US', 'France', 'Romania', 'US', 'France', 'US', 'France', 'Italy', 'US', 'Italy', 'US', 'US', 'US', 'US', 'US', 'US', 'US', 'Spain', 'France', 'France', 'US', 'France', 'France', 'France', 'US', 'US', 'US', 'Italy', 'US', 'US', 'US', 'US', 'France', 'US', 'US', 'US', 'US', 'US', 'US', 'Italy', 'US', 'Spain', 'US', 'Spain', 'US', 'US', 'Italy', 'France', 'France', 'France', 'US', 'Chile', 'Germany', 'US', 'US', 'France', 'Germany', 'France', 'US', 'US', 'US', 'US', 'US', 'US', 'nan', 'France', 'France', 'France', 'US', 'US', 'Slovenia', 'Italy', 'Italy', 'US', 'US', 'US', 'US', 'US', 'US', 'Italy', 'Moldova', 'US', 'US', 'France', 'Italy', 'US', 'US', 'India', 'US', 'US', 'US', 'Italy', 'Italy', 'Spain', 'Italy', 'Italy', 'Italy', 'US', 'US', 'France', 'US', 'US', 'New Zealand', 'France', 'France', 'US', 'US', 'US', 'US', 'US', 'Austria', 'US', 'Austria', 'US', 'Argentina', 'New Zealand', 'New Zealand', 'US', 'US', 'US', 'Spain', 'Spain', 'Spain', 'France', 'US', 'Italy', 'US', 'US', 'Austria', 'Austria', 'US', 'US', 'US', 'Germany', 'Italy', 'Italy', 'Israel', 'Portugal', 'US', 'Italy', 'US', 'Germany', 'France', 'France', 'US', 'Italy', 'Italy', 'Italy', 'Italy', 'Italy', 'Israel', 'US', 'US', 'France', 'Italy', 'Italy', 'US', 'US', 'US', 'US', 'US', 'France', 'US', 'US', 'US', 'Portugal', 'France', 'France', 'France', 'France', 'France', 'Portugal', 'France', 'France', 'Italy', 'Italy', 'US', 'US', 'US', 'Portugal', 'US', 'US', 'Chile', 'US', 'Portugal', 'US', 'US', 'US', 'Portugal', 'Italy', 'France', 'Portugal', 'South Africa', 'South Africa', 'France', 'Argentina', 'South Africa', 'US', 'France', 'US', 'France', 'France', 'France', 'US', 'US', 'Portugal', 'Portugal', 'US', 'Spain', 'US', 'Argentina', 'France', 'US', 'France', 'Portugal', 'Portugal', 'Portugal', 'Italy', 'France', 'Portugal', 'US', 'US', 'France', 'France', 'France', 'US', 'US', 'US', 'US', 'Italy', 'US', 'Italy', 'US', 'Spain', 'US', 'US', 'Argentina', 'Argentina', 'Argentina', 'Italy', 'Spain', 'US', 'Italy', 'France', 'France', 'France', 'France', 'France', 'France', 'US', 'US', 'Spain', 'Italy', 'US', 'France', 'Portugal', 'France', 'US', 'France', 'Germany', 'Spain', 'Spain', 'Greece', 'US', 'US', 'France', 'US', 'US', 'US', 'Italy', 'Italy', 'Portugal', 'France', 'US', 'US', 'US', 'US', 'US', 'US', 'US', 'Chile', 'France', 'US', 'Italy', 'US', 'Germany', 'Chile', 'US', 'Portugal', 'France', 'US', 'France', 'US', 'US', 'US', 'France', 'France', 'France', 'France', 'US', 'Portugal', 'France', 'France', 'France', 'US', 'Portugal', 'US', 'France', 'Italy', 'Portugal', 'Portugal', 'US', 'Spain', 'US', 'Argentina', 'France', 'US', 'Italy', 'US', 'Italy', 'US', 'France', 'US', 'Argentina', 'US', 'US', 'US', 'France', 'US', 'US', 'Italy', 'Spain', 'Spain', 'US', 'US', 'US', 'US', 'Spain', 'Italy', 'US', 'US', 'Italy', 'US', 'Hungary', 'US', 'US', 'Italy', 'US', 'Greece', 'US', 'US', 'US', 'US', 'US', 'US', 'France', 'Italy', 'US', 'Germany', 'US', 'France', 'US', 'US', 'US', 'US', 'US', 'Spain', 'Spain', 'US', 'Germany', 'Spain', 'nan', 'Italy', 'US', 'France', 'Italy', 'US', 'France', 'US', 'US', 'US', 'France', 'France', 'US', 'Spain', 'Spain', 'US', 'US', 'US', 'US', 'US', 'US', 'Italy', 'Spain', 'US', 'US', 'US', 'France', 'US', 'US', 'Hungary', 'US', 'US', 'US', 'Germany', 'Italy', 'Italy', 'Israel', 'Argentina', 'US', 'Italy', 'Argentina', 'Italy', 'US', 'Italy', 'France', 'France', 'France', 'France', 'France', 'US', 'US', 'Italy', 'US', 'Germany', 'Italy', 'US', 'Spain', 'Portugal', 'US', 'US', 'US', 'US', 'US', 'New Zealand', 'France', 'France', 'France', 'France', 'US', 'US', 'US', 'Austria', 'US', 'Austria', 'US', 'US', 'US', 'US', 'US', 'France', 'France', 'US', 'US', 'US', 'US', 'US', 'US', 'US', 'US', 'US', 'Portugal', 'Portugal', 'Portugal', 'Italy', 'Italy', 'US', 'Argentina', 'France', 'Argentina', 'Portugal', 'Portugal', 'US', 'Portugal', 'Portugal', 'France', 'Argentina', 'Spain', 'US', 'Portugal', 'US', 'France', 'US', 'Argentina', 'US', 'South Africa', 'Argentina', 'South Africa', 'Spain', 'Portugal', 'Portugal', 'US', 'US', 'US', 'US', 'Portugal', 'US', 'US', 'Portugal', 'US', 'US', 'US', 'France', 'France', 'France', 'Chile', 'US', 'US', 'US', 'Chile', 'US', 'Portugal', 'US', 'France', 'US', 'US', 'US', 'Portugal', 'US', 'Portugal', 'France', 'US', 'US', 'US', 'US', 'Italy', 'US', 'Argentina', 'US', 'Italy', 'Italy', 'Italy', 'Italy', 'Italy', 'Italy', 'US', 'Argentina', 'US', 'US', 'France', 'Spain', 'US', 'US', 'US', 'US', 'US', 'US', 'US', 'US', 'US', 'US', 'France', 'France', 'France', 'Italy', 'US', 'US', 'US', 'US', 'US', 'US', 'US', 'US', 'Italy', 'France', 'France', 'France', 'France', 'Italy', 'Italy', 'US', 'Portugal', 'Portugal', 'US', 'Portugal', 'US', 'US', 'Germany', 'Germany', 'Germany', 'Germany', 'US', 'US', 'US', 'US', 'US', 'US', 'Italy', 'Italy', 'Italy', 'Portugal', 'Chile', 'US', 'Italy', 'US', 'France', 'Chile', 'US', 'France', 'France', 'France', 'Italy', 'Chile', 'Chile', 'Italy', 'Italy', 'US', 'Chile', 'US', 'Germany', 'Spain', 'US', 'Portugal', 'US', 'Portugal', 'US', 'US', 'Croatia', 'Romania', 'France', 'France', 'US', 'US', 'US', 'US', 'Portugal', 'Portugal', 'France', 'France', 'US', 'Argentina', 'US', 'US', 'Italy', 'Spain', 'Spain', 'Spain', 'Spain', 'Spain', 'US', 'France', 'US', 'Germany', 'Chile', 'France', 'US', 'US', 'US', 'US', 'Chile', 'US', 'US', 'US', 'US', 'US', 'US', 'Germany', 'US', 'France', 'France', 'US', 'France', 'US', 'France', 'US', 'Spain', 'France', 'US', 'France', 'France', 'France', 'Hungary', 'US', 'US', 'France', 'US', 'US', 'US', 'Italy', 'Italy', 'Morocco', 'US', 'Moldova'] , 
    'province': ['California', 'Northern Spain', 'California', 'Oregon', 'Provence', 'Northern Spain', 'Northern Spain', 'Northern Spain', 'Oregon', 'California', 'Northeastern Italy', 'Oregon', 'Oregon', 'Southwest France', 'Oregon', 'Oregon', 'California', 'Northern Spain', 'Southwest France', 'California', 'California', 'Northern Spain', 'Northern Spain', 'California', 'California', 'Kumeu', 'Oregon', 'Oregon', 'California', 'Washington', 'Bulgaria', 'California', 'Tuscany', 'France Other', 'Washington', 'Tuscany', 'Rhône Valley', 'Tuscany', 'Tuscany', 'Tuscany', 'Galicia', 'Andalucia', 'Idaho', 'Tuscany', 'Rhône Valley', 'Tuscany', 'Tuscany', 'California', 'Tuscany', 'Washington', 'Tuscany', 'Burgundy', 'Loire Valley', 'Loire Valley', 'California', 'Washington', 'Loire Valley', 'New York', 'Washington', 'Tuscany', 'Mendoza Province', 'Victoria', 'Mendoza Province', 'Burgundy', 'Alentejano', 'California', 'Burgundy', 'California', 'Oregon', 'California', 'California', 'California', 'Piedmont', 'Oregon', 'Alentejo', 'Oregon', 'Champagne', 'California', 'California', 'Piedmont', 'Oregon', 'Upper Galilee', 'Piedmont', 'Piedmont', 'Piedmont', 'Piedmont', 'Burgundy', 'California', 'California', 'California', 'California', 'Beira Atlantico', 'Veneto', 'California', 'Douro', 'Southwest France', 'California', 'California', 'Southwest France', 'Southwest France', 'California', 'California', 'Tuscany', 'California', 'California', 'Washington', 'California', 'California', 'California', 'California', 'Tejo', 'Mendoza Province', 'California', 'New York', 'Stellenbosch', 'Mendoza Province', 'Levante', 'Southwest France', 'Southwest France', 'Alentejano', 'California', 'California', 'California', 'California', 'California', 'California', 'California', 'California', 'Northern Spain', 'Sicily & Sardinia', 'Southern Italy', 'California', 'California', 'California', 'California', 'California', 'California', 'California', 'Northern Spain', 'Languedoc-Roussillon', 'Bordeaux', 'California', 'California', 'Oregon', 'California', 'California', 'California', 'Galicia', 'California', 'California', 'Oregon', 'Atalanti Valley', 'Catalonia', 'Santorini', 'Florina', 'Marchigue', 'Southwest France', 'Oregon', 'Northern Spain', 'Colchagua Valley', 'California', 'Oregon', 'Northern Spain', 'California', 'California', 'Oregon', 'Tuscany', 'Tuscany', 'Douro', 'California', 'California', 'Curicó Valley', 'Nemea', 'California', 'Rhône Valley', 'Northern Spain', 'Tuscany', 'Tuscany', 'California', 'Maule Valley', 'California', 'California', 'California', 'Washington', 'Mendoza Province', 'Washington', 'California', 'California', 'Northern Spain', 'Catalonia', 'Mendoza Province', 'Bordeaux', 'Bordeaux', 'Bordeaux', 'Bordeaux', 'Bordeaux', 'California', 'Washington', 'New York', 'New York', 'New York', 'New York', 'Bordeaux', 'Bordeaux', 'Washington', 'Washington', 'Washington', 'New York', 'Washington', 'Catalonia', 'Douro', 'Piedmont', 'California', 'Piedmont', 'Alsace', 'Alsace', 'Guerrouane', 'Piedmont', 'Alsace', 'Alsace', 'Washington', 'California', 'Alsace', 'California', 'Piedmont', 'Bordeaux', 'California', 'Washington', 'California', 'Douro', 'Washington', 'California', 'Washington', 'Washington', 'Piedmont', 'Alsace', 'Alsace', 'Alsace', 'Alentejano', 'Piedmont', 'Bordeaux', 'Bordeaux', 'Bordeaux', 'Bordeaux', 'Bordeaux', 'California', 'Oregon', 'Colinele Dobrogei', 'California', 'California', 'California', 'Piedmont', 'Oregon', 'California', 'Oregon', 'Piedmont', 'California', 'California', 'Piedmont', 'Northern Spain', 'Central Spain', 'Loire Valley', 'California', 'California', 'Piedmont', 'Loire Valley', 'California', 'California', 'California', 'Mendoza Province', 'Burgundy', 'Burgundy', 'California', 'California', 'California', 'California', 'Northeastern Italy', 'Vinho Verde', 'Douro', 'California', 'Veneto', 'Northeastern Italy', 'Southwest France', 'Bordeaux', 'California', 'California', 'Burgundy', 'Southwest France', 'Burgundy', 'Oregon', 'Burgundy', 'Alentejano', 'Oregon', 'California', 'Southwest France', 'California', 'Northeastern Italy', 'Northeastern Italy', 'California', 'California', 'Washington', 'California', 'Veneto', 'California', 'California', 'Kumeu', 'Oregon', 'California', 'California', 'Oregon', 'California', 'Veneto', 'Veneto', 'California', 'Oregon', 'California', 'California', 'Oregon', 'Southwest France', 'Washington', 'Provence', 'Northern Spain', 'Provence', 'Northern Spain', 'California', 'Provence', 'Mendoza Province', 'Provence', 'Southwest France', 'Oregon', 'Piedmont', 'Mosel', 'California', 'Galicia', 'California', 'Alentejano', 'California', 'Oregon', 'California', 'Piedmont', 'Piedmont', 'California', 'Piedmont', 'California', 'Alentejano', 'Alentejano', 'California', 'California', 'Rheinhessen', 'Piedmont', 'California', 'Oregon', 'Champagne', 'Alentejo', 'Oregon', 'Golan Heights', 'California', 'Oregon', 'Piedmont', 'Northern Spain', 'California', 'California', 'Oregon', 'Alsace', 'Burgundy', 'Oregon', 'Sicily & Sardinia', 'Württemberg', 'Alsace', 'Alsace', 'Alsace', 'Oregon', 'Oregon', 'Burgundy', 'Sicily & Sardinia', 'Sicily & Sardinia', 'Oregon', 'Southern Italy', 'Mosel', 'California', 'California', 'California', 'California', 'Northern Spain', 'Ahr', 'Central Spain', 'California', 'California', 'California', 'California', 'California', 'California', 'Tuscany', 'Washington', 'British Columbia', 'Galicia', 'Loire Valley', 'Tuscany', 'Tuscany', 'Moldova', 'Tuscany', 'Tuscany', 'Tuscany', 'California', 'Rhône Valley', 'Rhône Valley', 'California', 'California', 'California', 'California', 'Spain Other', 'Sopron', 'Tuscany', 'California', 'California', 'California', 'California', 'Tuscany', 'Tuscany', 'Tuscany', 'Washington', 'California', 'New York', 'Washington', 'Catalonia', 'Northern Spain', 'Washington', 'Bordeaux', 'California', 'California', 'Idaho', 'Washington', 'Tuscany', 'Tuscany', 'Bordeaux', 'California', 'Idaho', 'Idaho', 'Tuscany', 'Andalucia', 'Tuscany', 'Idaho', 'Northern Spain', 'Andalucia', 'Northern Spain', 'Idaho', 'Catalonia', 'Tuscany', 'Tuscany', 'Tuscany', 'Douro', 'Veneto', 'California', 'California', 'Tejo', 'Other', 'California', 'Douro', 'Washington', 'California', 'Mendoza Province', 'Walker Bay', 'California', 'California', 'Washington', 'California', 'Southwest France', 'Mendoza Province', 'California', 'Mendoza Province', 'California', 'Alentejano', 'California', 'Dão', 'California', 'California', 'Southwest France', 'California', 'Tejo', 'Douro', 'California', 'Nemea', 'Rhône Valley', 'Tuscany', 'Southwest France', 'Southwest France', 'Mosel', 'Italy Other', 'Oregon', 'California', 'Tuscany', 'Southwest France', 'Oregon', 'Oregon', 'California', 'Duriense', 'California', 'Tuscany', 'Tuscany', 'Catalonia', 'Rhône Valley', 'California', 'Colchagua Valley', 'Oregon', 'California', 'Oregon', 'Galicia', 'Tuscany', 'Northern Spain', 'Catalonia', 'California', 'Alsace', 'Douro', 'California', 'California', 'California', 'California', 'Ontario', 'California', 'Douro', 'California', 'Beiras', 'Washington', 'California', 'Washington', 'Alsace', 'Alsace', 'California', 'California', 'Tokaji', 'Piedmont', 'California', 'Piedmont', 'Bordeaux', 'Lisboa', 'Alsace', 'California', 'Colchagua Valley', 'Washington', 'California', 'California', 'California', 'Mosel', 'Burgundy', 'Burgundy', 'California', 'California', 'Mosel', 'California', 'Sicily & Sardinia', 'Burgundy', 'Alsace', 'Burgundy', 'Alsace', 'Alsace', 'Oregon', 'Sicily & Sardinia', 'California', 'Sicily & Sardinia', 'Santorini', 'Oregon', 'California', 'Sicily & Sardinia', 'California', 'Northern Spain', 'Northern Spain', 'California', 'Mosel', 'California', 'California', 'California', 'Oregon', 'Southwest France', 'California', 'California', 'California', 'Northeastern Italy', 'Southwest France', 'California', 'Oregon', 'Southwest France', 'California', 'Thermenregion', 'Washington', 'California', 'California', 'Northern Spain', 'Burgenland', 'Carnuntum', 'California', 'California', 'Oregon', 'California', 'California', 'California', 'Burgenland', 'California', 'California', 'Northern Spain', 'Provence', 'California', 'Oregon', 'California', 'Douro', 'Northeastern Italy', 'California', 'Rheingau', 'Mosel', 'Rheingau', 'Nahe', 'Mosel', 'Northeastern Italy', 'Oregon', 'Alentejano', 'California', 'Burgundy', 'California', 'California', 'California', 'Mosel', 'Mosel', 'Mosel', 'Mosel', 'Mosel', 'Mosel', 'California', 'Northeastern Italy', 'Bordeaux', 'Dão', 'Burgundy', 'California', 'South Australia', 'Piedmont', 'Douro', 'Piedmont', 'California', 'California', 'Piedmont', 'Piedmont', 'Piedmont', 'Piedmont', 'Galicia', 'California', 'Southwest France', 'Douro', 'Oregon', 'California', 'Southwest France', 'Burgundy', 'Mosel', 'California', 'Piedmont', 'Oregon', 'Piedmont', 'Oregon', 'California', 'Oregon', 'Piedmont', 'Piedmont', 'Piedmont', 'Victoria', 'Loire Valley', 'Mendoza Province', 'Loire Valley', 'California', 'California', 'Bordeaux', 'California', 'Loire Valley', 'Piedmont', 'California', 'California', 'Loire Valley', 'California', 'Oregon', 'California', 'North Dalmatia', 'Piedmont', 'California', 'Bordeaux', 'Bordeaux', 'Bordeaux', 'Bordeaux', 'California', 'Bordeaux', 'Oregon', 'California', 'California', 'Loire Valley', 'Central Spain', 'California', 'Catalonia', 'Thracian Valley', 'California', 'California', 'California', 'New York', 'New York', 'Washington', 'Tuscany', 'California', 'Tuscany', 'California', 'California', 'California', 'British Columbia', 'California', 'California', 'California', 'California', 'Washington', 'Goriska Brda', 'California', 'Tuscany', 'British Columbia', 'California', 'Andalucia', 'Tuscany', 'California', 'Rhône Valley', 'California', 'Stellenbosch', 'Mendoza Province', 'Other', 'Western Cape', 'California', 'Southwest France', 'Southwest France', 'California', 'Burgundy', 'Northeastern Italy', 'Tejo', 'Southwest France', 'Southwest France', 'Western Cape', 'California', 'California', 'Mendoza Province', 'Veneto', 'Mendoza Province', 'Dão', 'Overberg', 'Mendoza Province', 'Northern Spain', 'Robertson', 'Rhône Valley', 'Mendoza Province', 'California', 'Thracian Valley', 'Galilee', 'Southwest France', 'Catalonia', 'California', 'California', 'California', 'Southwest France', 'California', 'Tuscany', 'California', 'Tuscany', 'Maipo Valley', 'California', 'Oregon', 'Oregon', 'Casablanca Valley', 'Tuscany', 'Cachapoal Valley', 'Oregon', 'California', 'Tuscany', 'Colchagua Valley', 'Oregon', 'Oregon', 'California', 'Tuscany', 'Douro', 'Terras do Dão', 'Alentejano', 'Leyda Valley', 'Southwest France', 'Tuscany', 'Tuscany', 'Washington', 'Tuscany', 'Washington', 'Bordeaux', 'Bordeaux', 'Bordeaux', 'Bordeaux', 'Bordeaux', 'California', 'Tuscany', 'California', 'California', 'Washington', 'Bordeaux', 'Washington', 'California', 'California', 'Washington', 'California', 'Idaho', 'Washington', 'California', 'California', 'California', 'New York', 'New York', 'California', 'Bordeaux', 'Sicily & Sardinia', 'Santorini', 'Oregon', 'California', 'Sicily & Sardinia', 'Burgundy', 'Alsace', 'Burgundy', 'Alsace', 'Alsace', 'Sicily & Sardinia', 'Oregon', 'California', 'California', 'Sicily & Sardinia', 'South Australia', 'California', 'California', 'California', 'California', 'California', 'California', 'California', 'Peumo', 'Northern Spain', 'California', 'California', 'California', 'Mosel', 'California', 'California', 'Catalonia', 'New York', 'California', 'Catalonia', 'California', 'New York', 'Burgundy', 'Loire Valley', 'Loire Valley', 'California', 'British Columbia', 'Thracian Valley', 'Burgundy', 'Loire Valley', 'California', 'Tuscany', 'Rhône Valley', 'Galicia', 'Andalucia', 'Tuscany', 'California', 'Tuscany', 'Tuscany', 'Northern Spain', 'Tuscany', 'Tuscany', 'Tuscany', 'Tuscany', 'California', 'Washington', 'California', 'California', 'Colchagua Valley', 'Piedmont', 'Alsace', 'Piedmont', 'Piedmont', 'California', 'California', 'Piedmont', 'Piedmont', 'Dão', 'Douro', 'Alsace', 'Washington', 'California', 'California', 'Washington', 'California', 'Washington', 'California', 'Colchagua Valley', 'Washington', 'California', 'Washington', 'California', 'Italy Other', 'Piedmont', 'Alsace', 'Mendoza Province', 'California', 'California', 'Southwest France', 'California', 'California', 'California', 'Provence', 'Provence', 'Southwest France', 'Provence', 'Provence', 'California', 'California', 'California', 'Oregon', 'California', 'California', 'Oregon', 'Andalucia', 'Oregon', 'California', 'Southwest France', 'California', 'Northern Spain', 'California', 'California', 'Oregon', 'California', 'California', 'Tuscany', 'Douro', 'Terras do Dão', 'Alentejano', 'Southwest France', 'California', 'Leyda Valley', 'Southwest France', 'Leyda Valley', 'California', 'Catalonia', 'California', 'Baden', 'Limarxad Valley', 'Lombardy', 'California', 'Tuscany', 'Oregon', 'Colchagua Valley', 'Tuscany', 'Douro', 'Tuscany', 'Oregon', 'California', 'Tuscany', 'Tuscany', 'Oregon', 'Douro', 'California', 'Peloponnese', 'Piedmont', 'Oregon', 'Douro', 'California', 'Northern Spain', 'Piedmont', 'Galilee', 'California', 'Mosel', 'California', 'Galilee', 'Piedmont', 'Alentejano', 'California', 'Galilee', 'California', 'Oregon', 'Judean Hills', 'Piedmont', 'California', 'Piedmont', 'Piedmont', 'Piedmont', 'Piedmont', 'Piedmont', 'Northern Spain', 'Piedmont', 'Tasmania', 'Oregon', 'Oregon', 'Veneto', 'California', 'Galilee', 'Vinho Verde', 'Vinho Verde', 'Tejo', 'Beira Atlantico', 'Southwest France', 'Southwest France', 'Mendoza Province', 'Tejo', 'California', 'California', 'Dão', 'Alentejano', 'Bairrada', 'Stellenbosch', 'Mendoza Province', 'Western Cape', 'Rhône Valley', 'California', 'Simonsberg-Paarl', 'Southwest France', 'Southwest France', 'Southwest France', 'Portuguese Table Wine', 'Alentejano', 'Burgundy', 'California', 'Veneto', 'Rheinhessen', 'Oregon', 'Northeastern Italy', 'Oregon', 'Beaujolais', 'Tejo', 'Penxadnsula de Setúbal', 'Alentejano', 'California', 'California', 'Douro', 'Douro', 'Mosel', 'Tejo', 'Bordeaux', 'Beaujolais', 'Württemberg', 'Colchagua Valley', 'Colchagua Valley', 'Lombardy', 'Oregon', 'Aconcagua Valley', 'Tuscany', 'Douro', 'California', 'Tejo', 'Alentejano', 'Alentejano', 'Douro', 'California', 'Piedmont', 'Piedmont', 'Oregon', 'California', 'Oregon', 'Virginia', 'Virginia', 'Other', 'California', 'Other', 'Dão', 'Thracian Valley', 'California', 'Piedmont', 'Other', 'Northern Spain', 'South Australia', 'Virginia', 'North Dalmatia', 'California', 'Bordeaux', 'Dealurile Munteniei', 'California', 'Loire Valley', 'California', 'Loire Valley', 'Piedmont', 'California', 'Piedmont', 'California', 'California', 'California', 'New York', 'Washington', 'Washington', 'New York', 'Levante', 'Bordeaux', 'Bordeaux', 'New York', 'Bordeaux', 'Bordeaux', 'Bordeaux', 'Idaho', 'California', 'California', 'Tuscany', 'California', 'California', 'New York', 'Washington', 'Bordeaux', 'California', 'Washington', 'California', 'California', 'Washington', 'California', 'Tuscany', 'Washington', 'Northern Spain', 'California', 'Northern Spain', 'California', 'California', 'Sicily & Sardinia', 'Burgundy', 'Burgundy', 'Burgundy', 'California', 'Cachapoal Valley', 'Rheingau', 'California', 'Oregon', 'Alsace', 'Rheinhessen', 'Burgundy', 'California', 'California', 'California', 'California', 'Oregon', 'California', 'nan', 'Alsace', 'Alsace', 'Alsace', 'Oregon', 'California', 'Goriska Brda', 'Tuscany', 'Tuscany', 'California', 'California', 'California', 'California', 'Washington', 'California', 'Tuscany', 'Moldova', 'California', 'California', 'Loire Valley', 'Tuscany', 'New York', 'Washington', 'Nashik', 'California', 'California', 'California', 'Tuscany', 'Tuscany', 'Northern Spain', 'Tuscany', 'Tuscany', 'Tuscany', 'California', 'California', 'Burgundy', 'New York', 'California', 'Kumeu', 'Southwest France', 'Southwest France', 'California', 'California', 'California', 'Oregon', 'California', 'Burgenland', 'California', 'Niederösterreich', 'Washington', 'Mendoza Province', 'Marlborough', 'Central Otago', 'California', 'Oregon', 'California', 'Northern Spain', 'Northern Spain', 'Northern Spain', 'Provence', 'California', 'Southern Italy', 'California', 'Washington', 'Niederösterreich', 'Thermenregion', 'California', 'Oregon', 'Oregon', 'Mosel', 'Piedmont', 'Piedmont', 'Galilee', 'Lisboa', 'Oregon', 'Piedmont', 'California', 'Mosel', 'Burgundy', 'Burgundy', 'California', 'Piedmont', 'Piedmont', 'Piedmont', 'Piedmont', 'Piedmont', 'Galilee', 'California', 'California', 'Champagne', 'Piedmont', 'Piedmont', 'California', 'California', 'Oregon', 'Oregon', 'California', 'Alsace', 'California', 'California', 'California', 'Palmela', 'Alsace', 'Alsace', 'Alsace', 'Alsace', 'Alsace', 'Alentejano', 'Bordeaux', 'Bordeaux', 'Piedmont', 'Piedmont', 'California', 'California', 'Washington', 'Douro', 'Washington', 'California', 'Colchagua Valley', 'California', 'Dão', 'California', 'California', 'California', 'Douro', 'Piedmont', 'Bordeaux', 'Tejo', 'Robertson', 'Western Cape', 'Rhône Valley', 'Mendoza Province', 'Western Cape', 'California', 'Burgundy', 'California', 'Southwest France', 'Southwest France', 'Southwest France', 'Washington', 'California', 'Tejo', 'Tejo', 'Washington', 'Northern Spain', 'New York', 'Mendoza Province', 'Rhône Valley', 'New York', 'Southwest France', 'Alentejano', 'Alentejano', 'Douro', 'Veneto', 'Southwest France', 'Beira Interior', 'California', 'New York', 'Bordeaux', 'Bordeaux', 'Bordeaux', 'Idaho', 'California', 'California', 'Washington', 'Tuscany', 'Washington', 'Tuscany', 'Washington', 'Levante', 'Washington', 'New York', 'Mendoza Province', 'Mendoza Province', 'Mendoza Province', 'Tuscany', 'Catalonia', 'Idaho', 'Tuscany', 'Bordeaux', 'Bordeaux', 'Bordeaux', 'Bordeaux', 'Bordeaux', 'Bordeaux', 'California', 'New York', 'Northern Spain', 'Tuscany', 'Oregon', 'Southwest France', 'Tejo', 'Southwest France', 'Oregon', 'Southwest France', 'Mosel', 'Catalonia', 'Catalonia', 'Peloponnese', 'California', 'California', 'Southwest France', 'California', 'California', 'California', 'Tuscany', 'Lombardy', 'Port', 'Southwest France', 'Oregon', 'California', 'California', 'California', 'California', 'California', 'Oregon', 'Casablanca Valley', 'Southwest France', 'California', 'Lombardy', 'California', 'Mosel', 'Marchigue', 'Oregon', 'Bairrada', 'Burgundy', 'California', 'Burgundy', 'California', 'California', 'California', 'Bordeaux', 'Southwest France', 'Bordeaux', 'Bordeaux', 'California', 'Dão', 'Burgundy', 'Southwest France', 'Southwest France', 'Oregon', 'Alentejano', 'California', 'Burgundy', 'Lombardy', 'Vinho Verde', 'Tejo', 'California', 'Central Spain', 'Oregon', 'Mendoza Province', 'Bordeaux', 'California', 'Piedmont', 'California', 'Piedmont', 'Oregon', 'Loire Valley', 'Oregon', 'Mendoza Province', 'California', 'Oregon', 'Oregon', 'Loire Valley', 'California', 'California', 'Piedmont', 'Northern Spain', 'Northern Spain', 'California', 'Oregon', 'California', 'California', 'Northern Spain', 'Piedmont', 'Oregon', 'California', 'Sicily & Sardinia', 'Oregon', 'Tokaji', 'California', 'California', 'Southern Italy', 'California', 'Santorini', 'California', 'California', 'California', 'California', 'California', 'California', 'Alsace', 'Sicily & Sardinia', 'Oregon', 'Franken', 'Oregon', 'Alsace', 'Oregon', 'Oregon', 'California', 'California', 'California', 'Northern Spain', 'Northern Spain', 'California', 'Rheinhessen', 'Northern Spain', 'nan', 'Tuscany', 'Washington', 'Burgundy', 'Tuscany', 'California', 'Loire Valley', 'New York', 'California', 'California', 'France Other', 'Rhône Valley', 'California', 'Andalucia', 'Andalucia', 'California', 'California', 'California', 'California', 'California', 'California', 'Tuscany', 'Catalonia', 'California', 'California', 'California', 'Rhône Valley', 'California', 'California', 'Tokaji', 'Oregon', 'Oregon', 'Oregon', 'Mosel', 'Piedmont', 'Piedmont', 'Galilee', 'Mendoza Province', 'Oregon', 'Piedmont', 'Mendoza Province', 'Piedmont', 'California', 'Piedmont', 'Southwest France', 'Loire Valley', 'Southwest France', 'Southwest France', 'Southwest France', 'California', 'Oregon', 'Piedmont', 'California', 'Baden', 'Piedmont', 'California', 'Northern Spain', 'Alentejano', 'California', 'California', 'California', 'California', 'Oregon', 'Martinborough', 'Southwest France', 'Provence', 'Provence', 'Southwest France', 'Oregon', 'Oregon', 'California', 'Wagram', 'California', 'Kamptal', 'Oregon', 'California', 'California', 'California', 'Oregon', 'Provence', 'Southwest France', 'California', 'California', 'California', 'California', 'Oregon', 'Oregon', 'California', 'California', 'California', 'Alentejano', 'Alentejano', 'Douro', 'Veneto', 'Tuscany', 'Washington', 'Other', 'Southwest France', 'Mendoza Province', 'Alentejano', 'Tejo', 'California', 'Alentejano', 'Palmela', 'Rhône Valley', 'Mendoza Province', 'Northern Spain', 'California', 'Tejo', 'California', 'Southwest France', 'California', 'Mendoza Province', 'California', 'Stellenbosch', 'Mendoza Province', 'South Africa', 'Levante', 'Vinho Verde', 'Vinho Verde', 'California', 'Washington', 'California', 'Washington', 'Alentejano', 'Washington', 'California', 'Dão', 'California', 'Washington', 'California', 'Alsace', 'Alsace', 'Alsace', 'Aconcagua Valley', 'California', 'California', 'California', 'Rapel Valley', 'California', 'Bairrada', 'California', 'Bordeaux', 'California', 'California', 'California', 'Douro', 'California', 'Douro', 'Alsace', 'Washington', 'Washington', 'California', 'Washington', 'Tuscany', 'California', 'Mendoza Province', 'Washington', 'Tuscany', 'Tuscany', 'Tuscany', 'Tuscany', 'Tuscany', 'Tuscany', 'Washington', 'Mendoza Province', 'Washington', 'Washington', 'Bordeaux', 'Northern Spain', 'California', 'California', 'Washington', 'California', 'California', 'Washington', 'Washington', 'Washington', 'Washington', 'California', 'Champagne', 'Southwest France', 'Champagne', 'Tuscany', 'California', 'California', 'California', 'Oregon', 'California', 'California', 'California', 'California', 'Tuscany', 'Champagne', 'Bordeaux', 'Bordeaux', 'Bordeaux', 'Lombardy', 'Lombardy', 'California', 'Douro', 'Tejo', 'California', 'Tejo', 'California', 'California', 'Mosel', 'Rheingau', 'Mosel', 'Rheinhessen', 'California', 'California', 'California', 'California', 'California', 'California', 'Tuscany', 'Tuscany', 'Tuscany', 'Tejo', 'Casablanca Valley', 'California', 'Tuscany', 'Oregon', 'Southwest France', 'Maipo Valley', 'California', 'Southwest France', 'Southwest France', 'Southwest France', 'Tuscany', 'Maule Valley', 'Casablanca Valley', 'Tuscany', 'Tuscany', 'California', 'Cachapoal Valley', 'California', 'Pfalz', 'Northern Spain', 'California', 'Alentejano', 'Oregon', 'Douro', 'California', 'California', 'Hvar', 'Colinele Dobrogei', 'Loire Valley', 'Loire Valley', 'California', 'California', 'California', 'California', 'Vinho Verde', 'Douro', 'Loire Valley', 'Bordeaux', 'California', 'Other', 'California', 'Colorado', 'Piedmont', 'Northern Spain', 'Northern Spain', 'Catalonia', 'Northern Spain', 'Northern Spain', 'Arizona', 'Loire Valley', 'California', 'Rheinhessen', 'Colchagua Valley', 'Burgundy', 'California', 'California', 'California', 'California', 'Aconcagua Costa', 'California', 'California', 'California', 'Oregon', 'California', 'California', 'Rheingau', 'California', 'Alsace', 'Burgundy', 'Oregon', 'Bordeaux', 'California', 'Burgundy', 'California', 'Catalonia', 'Burgundy', 'Oregon', 'Alsace', 'Alsace', 'Alsace', 'Tokaji', 'California', 'New York', 'Loire Valley', 'California', 'California', 'California', 'Tuscany', 'Tuscany', 'Zenata', 'California', 'Moldova'],
    'points': ['96', '96', '96', '96', '95', '95', '95', '95', '95', '95', '95', '95', '95', '95', '95', '95', '95', '95', '95', '95', '95', '95', '95', '95', '95', '94', '94', '94', '94', '94', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '91', '91', '91', '91', '91', '91', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '88', '88', '88', '88', '88', '88', '88', '88', '88', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '92', '92', '92', '92', '92', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '94', '94', '94', '94', '94', '94', '94', '94', '94', '94', '94', '94', '94', '94', '94', '94', '94', '94', '94', '94', '94', '94', '94', '94', '94', '94', '94', '94', '94', '94', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '86', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '94', '94', '94', '94', '94', '94', '94', '94', '94', '94', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '86', '86', '86', '86', '86', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '89', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '93', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '85', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '89', '89', '89', '89', '89', '89', '89', '89', '89', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '93', '93', '93', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '85', '85', '85', '85', '85', '85', '85', '85', '84', '84', '84', '84', '84', '84', '84', '84', '84', '84', '84', '84', '84', '84', '84', '84', '84', '84', '84', '84', '84', '84', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '92', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '91', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '87', '91', '91', '91', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '88', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90', '90'],
    'price': ['235.0', '110.0', '90.0', '65.0', '66.0', '73.0', '65.0', '110.0', '65.0', '60.0', '80.0', '48.0', '48.0', '90.0', '185.0', '90.0', '325.0', '80.0', '290.0', '75.0', '24.0', '79.0', '220.0', '60.0', '45.0', '57.0', '62.0', '105.0', '60.0', '60.0', '15.0', '37.0', 'nan', '22.0', '42.0', '135.0', '60.0', '29.0', '23.0', '29.0', '17.0', '26.0', '55.0', '39.0', '69.0', '30.0', '90.0', '60.0', '50.0', '40.0', '100.0', '68.0', '42.0', '28.0', '18.0', '69.0', 'nan', '25.0', '30.0', '60.0', '30.0', '36.0', '25.0', '45.0', '23.0', '36.0', '38.0', '85.0', '50.0', '60.0', '85.0', '45.0', 'nan', '19.0', '15.0', '54.0', '85.0', '38.0', '28.0', '75.0', '42.0', '25.0', 'nan', '59.0', '85.0', '80.0', '45.0', '22.0', '65.0', '50.0', '10.0', '12.0', '22.0', '13.0', '10.0', '14.0', '18.0', '36.0', '15.0', '10.0', '24.0', '50.0', '45.0', '48.0', '20.0', '17.0', '12.0', '10.0', '13.0', '45.0', '12.0', '12.0', '125.0', '25.0', '20.0', '15.0', 'nan', '20.0', '15.0', '7.0', '59.0', '49.0', '42.0', '93.0', '32.0', '20.0', '100.0', '50.0', '22.0', '45.0', '18.0', '45.0', '26.0', '16.0', '30.0', '42.0', '38.0', '48.0', '17.0', '18.0', '15.0', '28.0', '25.0', '26.0', '24.0', '55.0', '36.0', '17.0', '40.0', '28.0', '50.0', '24.0', '17.0', '21.0', '18.0', '20.0', '20.0', '24.0', '44.0', '19.0', '42.0', '35.0', '44.0', '16.0', '23.0', '36.0', '25.0', '22.0', '20.0', '25.0', '42.0', '30.0', '17.0', '49.0', '16.0', '30.0', '40.0', '57.0', '29.0', '61.0', '25.0', '25.0', '49.0', '20.0', '26.0', '34.0', '38.0', '38.0', '25.0', '22.0', '15.0', '20.0', '25.0', '20.0', '20.0', '25.0', '10.0', '18.0', '18.0', '14.0', '14.0', '40.0', '18.0', '20.0', '10.0', '11.0', '36.0', '20.0', '32.0', '18.0', '55.0', '49.0', '50.0', '58.0', '39.0', '65.0', '35.0', '80.0', '42.0', '61.0', '58.0', '38.0', '48.0', '50.0', '58.0', '120.0', '50.0', '80.0', '40.0', '41.0', '48.0', '200.0', '39.0', '62.0', '43.0', '35.0', '48.0', '55.0', '40.0', '69.0', '16.0', '16.0', 'nan', '15.0', '13.0', '28.0', '36.0', '9.0', '24.0', '30.0', '25.0', '34.0', '60.0', '54.0', '15.0', '56.0', '20.0', '61.0', '46.0', '30.0', '17.0', 'nan', '40.0', '39.0', '49.0', '23.0', '16.0', '32.0', '18.0', '15.0', '92.0', '94.0', '58.0', '50.0', '48.0', '32.0', '27.0', '35.0', '95.0', '43.0', '33.0', '60.0', 'nan', '30.0', '100.0', '35.0', '60.0', '16.0', '40.0', '60.0', '100.0', '18.0', '16.0', '42.0', 'nan', '20.0', '25.0', '23.0', '38.0', '32.0', '60.0', '30.0', '85.0', '30.0', '65.0', '57.0', '90.0', '85.0', '70.0', '70.0', '60.0', '38.0', '29.0', '155.0', '48.0', '95.0', '80.0', '49.0', '35.0', '50.0', '44.0', '68.0', '20.0', 'nan', '95.0', '44.0', '50.0', '100.0', '70.0', '63.0', '75.0', '23.0', '50.0', '22.0', '45.0', '130.0', '38.0', '30.0', '22.0', 'nan', '90.0', '60.0', '115.0', '55.0', '30.0', '14.0', '48.0', '40.0', '39.0', '60.0', '50.0', '48.0', '54.0', '42.0', '50.0', '40.0', '40.0', '42.0', '85.0', '32.0', '41.0', '27.0', '29.0', '33.0', '70.0', '19.0', '22.0', '25.0', '27.0', '22.0', '30.0', '15.0', '45.0', '80.0', 'nan', 'nan', '18.0', '19.0', '31.0', '15.0', '15.0', '24.0', '80.0', '35.0', '40.0', '28.0', '50.0', '28.0', '36.0', '40.0', '50.0', '75.0', '60.0', '46.0', '70.0', '26.0', 'nan', '60.0', '75.0', '32.0', '95.0', '60.0', '70.0', '20.0', '27.0', '20.0', '75.0', '28.0', '60.0', '22.0', '49.0', '35.0', '90.0', '30.0', '35.0', '38.0', '22.0', '30.0', '32.0', '35.0', '36.0', '30.0', '20.0', '32.0', '18.0', '27.0', '20.0', 'nan', '30.0', '20.0', '23.0', '22.0', '75.0', '98.0', 'nan', '20.0', '22.0', '16.0', '28.0', '25.0', '17.0', '17.0', '15.0', '16.0', '15.0', '38.0', '28.0', '52.0', '58.0', '60.0', '15.0', '15.0', '26.0', '32.0', '10.0', '10.0', '18.0', '12.0', '35.0', '34.0', '23.0', '20.0', '31.0', '24.0', '12.0', '18.0', '10.0', '15.0', '24.0', '14.0', '14.0', '15.0', '38.0', '13.0', '12.0', '32.0', '15.0', '28.0', 'nan', '30.0', '49.0', '17.0', '11.0', '43.0', '19.0', '28.0', '26.0', 'nan', '35.0', '30.0', '55.0', 'nan', '46.0', '50.0', '43.0', '45.0', '39.0', '30.0', '45.0', '23.0', '15.0', '65.0', '19.0', '35.0', '60.0', '44.0', '25.0', '30.0', '12.0', '18.0', '30.0', 'nan', '23.0', '45.0', '125.0', '98.0', '40.0', '17.0', '60.0', '70.0', '68.0', '40.0', '32.0', '45.0', '66.0', '29.0', '63.0', '32.0', '55.0', '16.0', '45.0', '20.0', '50.0', '18.0', '23.0', 'nan', '32.0', '30.0', '35.0', '44.0', '24.0', '20.0', '22.0', '50.0', '45.0', '23.0', '49.0', '17.0', '35.0', 'nan', '59.0', '24.0', 'nan', '20.0', '20.0', '18.0', 'nan', '42.0', '22.0', '20.0', '48.0', '30.0', 'nan', '40.0', '20.0', '17.0', '22.0', '31.0', '15.0', '15.0', '62.0', '49.0', '25.0', '95.0', '55.0', '48.0', '35.0', '40.0', '68.0', '90.0', '25.0', '60.0', '21.0', '125.0', '85.0', '60.0', '64.0', '19.0', '25.0', '55.0', '58.0', '48.0', '40.0', '60.0', '120.0', 'nan', '100.0', '34.0', '91.0', '36.0', '40.0', '20.0', '55.0', '19.0', '26.0', '45.0', '36.0', '23.0', '25.0', '21.0', '28.0', '41.0', '26.0', 'nan', '28.0', 'nan', '38.0', '44.0', '45.0', '25.0', '38.0', '22.0', '26.0', '23.0', '23.0', '50.0', '21.0', '25.0', '16.0', '60.0', '38.0', '20.0', '75.0', '33.0', '75.0', '64.0', '18.0', '75.0', '30.0', '42.0', '18.0', '20.0', '40.0', '25.0', '19.0', '18.0', '30.0', '13.0', '45.0', '30.0', '111.0', '35.0', '32.0', '88.0', '57.0', '34.0', '24.0', '45.0', '74.0', 'nan', '42.0', '27.0', '25.0', '35.0', '45.0', '30.0', '26.0', '39.0', '25.0', '80.0', '55.0', '22.0', '28.0', '25.0', '48.0', '19.0', '19.0', '77.0', '18.0', '25.0', 'nan', 'nan', '18.0', '18.0', 'nan', '65.0', '25.0', '48.0', '20.0', '11.0', '55.0', '35.0', '26.0', '46.0', '55.0', '30.0', '25.0', '27.0', '28.0', '62.0', '48.0', '80.0', '36.0', '48.0', '60.0', '24.0', '42.0', '45.0', '39.0', '25.0', '40.0', '40.0', '40.0', '60.0', '19.0', '85.0', '26.0', '25.0', '15.0', '24.0', '18.0', '35.0', '26.0', '39.0', '11.0', '15.0', '9.0', '16.0', '15.0', '18.0', '9.0', '11.0', '12.0', '14.0', '10.0', '12.0', '18.0', '14.0', '10.0', '13.0', '10.0', '20.0', '30.0', '50.0', '16.0', '11.0', '15.0', '65.0', '9.0', '30.0', 'nan', '26.0', '20.0', '25.0', '36.0', '14.0', '36.0', '23.0', '30.0', '28.0', '20.0', '36.0', '45.0', '20.0', '20.0', '45.0', '20.0', '28.0', '42.0', '110.0', '25.0', '14.0', '18.0', '39.0', '90.0', '18.0', '7.0', '17.0', '17.0', '20.0', '50.0', '87.0', '28.0', 'nan', '36.0', 'nan', 'nan', '35.0', 'nan', '30.0', '28.0', '20.0', '18.0', '32.0', '28.0', 'nan', '26.0', '32.0', '11.0', '26.0', '19.0', '22.0', '28.0', '28.0', '20.0', '25.0', '16.0', '18.0', '25.0', '10.0', '22.0', '20.0', '48.0', '30.0', 'nan', '59.0', '24.0', 'nan', '20.0', '20.0', 'nan', '18.0', '70.0', '25.0', '36.0', '65.0', '42.0', '50.0', '28.0', '22.0', '26.0', '80.0', '28.0', '24.0', '21.0', '50.0', '40.0', '22.0', '30.0', '50.0', '55.0', '35.0', '37.0', '42.0', '25.0', '60.0', '27.0', '45.0', '20.0', 'nan', '48.0', '38.0', '28.0', '80.0', '19.0', '45.0', '56.0', '24.0', '36.0', '26.0', '25.0', '15.0', '22.0', '20.0', '30.0', '30.0', '18.0', '22.0', '28.0', '40.0', '35.0', '44.0', '32.0', '30.0', '113.0', '30.0', '92.0', '75.0', '50.0', '27.0', '49.0', '19.0', '11.0', '44.0', '24.0', '15.0', '35.0', '33.0', '140.0', '35.0', '75.0', '40.0', '100.0', '21.0', '80.0', '28.0', '40.0', '40.0', '500.0', '55.0', '40.0', '40.0', '65.0', '65.0', 'nan', '28.0', '51.0', '50.0', '34.0', '50.0', '30.0', '40.0', '30.0', '45.0', '32.0', '125.0', '150.0', '60.0', '70.0', '30.0', '60.0', '80.0', '25.0', '32.0', '61.0', '60.0', '45.0', '60.0', '80.0', '85.0', '90.0', '18.0', '7.0', '17.0', '18.0', '39.0', '17.0', '20.0', '22.0', '25.0', '50.0', '31.0', '25.0', '26.0', '27.0', '25.0', '22.0', '18.0', '20.0', '65.0', '60.0', '52.0', '25.0', '65.0', '240.0', '35.0', '40.0', '18.0', '26.0', '13.0', 'nan', '28.0', '18.0', '40.0', '35.0', '38.0', '20.0', '72.0', '60.0', '44.0', '15.0', '70.0', '30.0', '36.0', '40.0', '70.0', '48.0', '55.0', '42.0', '125.0', '110.0', '103.0', '100.0', '40.0', '68.0', '24.0', '52.0', '65.0', '37.0', '28.0', 'nan', '13.0', '30.0', '10.0', '9.0', '7.0', '12.0', '15.0', '9.0', '11.0', '28.0', '20.0', '18.0', '11.0', '7.0', '8.0', '22.0', '12.0', '10.0', '16.0', '100.0', '15.0', '16.0', '12.0', '15.0', '10.0', '9.0', '12.0', '30.0', 'nan', '17.0', '65.0', 'nan', '32.0', '24.0', '35.0', '17.0', '22.0', '36.0', '43.0', '28.0', '75.0', '20.0', '30.0', 'nan', 'nan', '24.0', '100.0', '30.0', '26.0', '65.0', '100.0', '30.0', 'nan', '48.0', 'nan', '26.0', 'nan', '16.0', '42.0', '60.0', '56.0', '19.0', '21.0', '20.0', '25.0', '72.0', '18.0', '70.0', '29.0', '35.0', '10.0', '26.0', '28.0', '12.0', '25.0', '25.0', '19.0', '27.0', '12.0', '15.0', '9.0', '22.0', '37.0', '19.0', 'nan', 'nan', '40.0', 'nan', '70.0', '34.0', '38.0', '14.0', '20.0', '30.0', '40.0', '15.0', '20.0', 'nan', '25.0', '35.0', 'nan', '20.0', '23.0', '24.0', '16.0', '24.0', '20.0', '12.0', '20.0', '28.0', '27.0', '22.0', '50.0', '28.0', '25.0', '40.0', '18.0', '23.0', '14.0', '15.0', '26.0', '20.0', '20.0', '50.0', 'nan', 'nan', '56.0', 'nan', '42.0', '27.0', '30.0', '28.0', '32.0', '35.0', '19.0', '70.0', '25.0', '40.0', '90.0', '45.0', '19.0', '25.0', '17.0', '15.0', '45.0', '21.0', '22.0', '56.0', '15.0', 'nan', '70.0', '40.0', '85.0', '24.0', '26.0', '46.0', '24.0', '85.0', '32.0', '36.0', '16.0', '35.0', '80.0', '20.0', '15.0', '13.0', '20.0', '75.0', '55.0', '22.0', '20.0', '30.0', '30.0', '18.0', '22.0', '35.0', '48.0', '43.0', '18.0', '32.0', '46.0', '40.0', '20.0', '55.0', '94.0', '40.0', '37.0', '44.0', 'nan', '50.0', '27.0', '32.0', '38.0', '33.0', '40.0', '36.0', '35.0', '60.0', '37.0', '44.0', '136.0', '52.0', '48.0', '80.0', '30.0', '32.0', 'nan', '19.0', '65.0', '50.0', '32.0', '23.0', 'nan', '44.0', '40.0', '13.0', '15.0', 'nan', '50.0', '22.0', '141.0', '74.0', '100.0', '102.0', '80.0', '35.0', '55.0', '50.0', '38.0', '42.0', '26.0', '65.0', '70.0', '60.0', '50.0', '44.0', '60.0', '20.0', '45.0', '34.0', '55.0', '75.0', '34.0', '17.0', '25.0', '30.0', '47.0', '49.0', '26.0', '53.0', '65.0', '40.0', '34.0', '55.0', '60.0', '100.0', '39.0', '25.0', '42.0', '65.0', '85.0', '43.0', '35.0', '100.0', '70.0', '80.0', '25.0', '65.0', '65.0', '15.0', '10.0', '15.0', '63.0', '35.0', '10.0', '32.0', 'nan', '18.0', '11.0', '9.0', '12.0', '18.0', '52.0', '15.0', '15.0', '27.0', '30.0', '15.0', '13.0', '13.0', '25.0', '17.0', '10.0', '7.0', '14.0', '10.0', '9.0', '10.0', '20.0', '25.0', '35.0', 'nan', '20.0', '23.0', '24.0', '16.0', '32.0', '55.0', '13.0', '42.0', '74.0', '15.0', '35.0', '20.0', '11.0', '38.0', '18.0', '75.0', '10.0', '18.0', '40.0', '30.0', 'nan', '40.0', '13.0', '19.0', '25.0', '21.0', '18.0', '34.0', '32.0', '33.0', '22.0', '12.0', '26.0', '22.0', '13.0', '45.0', '25.0', '22.0', '19.0', '20.0', '96.0', 'nan', '28.0', '19.0', '26.0', '17.0', '35.0', '20.0', '18.0', '34.0', '14.0', '28.0', '66.0', '25.0', '28.0', '28.0', '13.0', 'nan', '24.0', '25.0', '36.0', '18.0', '23.0', '28.0', '40.0', '78.0', '43.0', '65.0', '44.0', '50.0', '56.0', 'nan', '30.0', 'nan', '22.0', '48.0', '22.0', '60.0', '40.0', 'nan', '19.0', 'nan', '64.0', '74.0', '24.0', 'nan', 'nan', '63.0', '14.0', '16.0', '21.0', '15.0', '18.0', '50.0', '18.0', '80.0', '48.0', '22.0', '16.0', '28.0', '35.0', '40.0', '48.0', '12.0', '20.0', '26.0', '55.0', '8.0', '16.0', '30.0', '23.0', '21.0', '30.0', '30.0', '35.0', '17.0', '25.0', '24.0', '40.0', '16.0', '40.0', '28.0', '21.0', '36.0', '28.0', '65.0', '49.0', '44.0', '48.0', '28.0', '30.0', '17.0', '39.0', '16.0', '22.0', '45.0', '15.0', '48.0', '35.0', '24.0', '95.0', '32.0', '26.0', '32.0', '24.0', '25.0', '50.0', '30.0', '60.0', '12.0', '50.0', '85.0', '42.0', '20.0', '72.0', '66.0', '18.0', '32.0', '19.0', '44.0', '90.0', '33.0', '45.0', '30.0', '65.0', '65.0', '125.0', '38.0', '28.0', '32.0', '55.0', '85.0', '35.0', '17.0', '48.0', '16.0', '26.0', '28.0', '50.0', '32.0', '23.0', 'nan', '44.0', '40.0', '30.0', '28.0', '46.0', '24.0', 'nan', '33.0', '25.0', '13.0', '16.0', '50.0', '19.0', '13.0', '50.0', '50.0', '35.0', '30.0', '25.0', 'nan', '40.0', '55.0', '100.0', '100.0', '28.0', '32.0', '40.0', '40.0', '63.0', '26.0', '45.0', 'nan', '25.0', '75.0', '95.0', '42.0', '17.0', '35.0', '18.0', '28.0', '54.0', '35.0', '40.0', '68.0', '59.0', '28.0', '40.0', '80.0', '38.0', '38.0', '63.0', '40.0', 'nan', '50.0', '34.0', '10.0', '7.0', '14.0', '10.0', '149.0', '26.0', '16.0', '9.0', '12.0', '18.0', 'nan', '15.0', '13.0', '12.0', '14.0', '12.0', '9.0', '29.0', '10.0', '35.0', '12.0', '14.0', '17.0', '12.0', '20.0', '17.0', '9.0', '14.0', '10.0', '10.0', '35.0', '32.0', '56.0', '39.0', '23.0', '40.0', '20.0', '32.0', '35.0', '52.0', '48.0', '14.0', '27.0', '38.0', '20.0', '40.0', '54.0', '26.0', '22.0', '30.0', '58.0', '40.0', '35.0', '24.0', '29.0', '80.0', '22.0', '15.0', '22.0', '36.0', '25.0', '22.0', '25.0', '32.0', '20.0', '35.0', '18.0', '13.0', '140.0', '60.0', '25.0', '50.0', '138.0', '55.0', '15.0', '12.0', '35.0', '23.0', '19.0', '15.0', '19.0', '24.0', '19.0', '48.0', '20.0', '26.0', '8.0', '60.0', '25.0', '20.0', '66.0', '45.0', '75.0', '25.0', '40.0', '95.0', '48.0', '48.0', '50.0', '28.0', '44.0', '60.0', '16.0', '50.0', '55.0', '20.0', '45.0', 'nan', '19.0', '50.0', '18.0', '15.0', '54.0', 'nan', '35.0', '45.0', '31.0', '35.0', '18.0', '60.0', '25.0', '25.0', '50.0', '30.0', '60.0', '15.0', '65.0', '19.0', '28.0', 'nan', '20.0', '27.0', '120.0', '20.0', '15.0', '12.0', '35.0', '12.0', '16.0', '45.0', '22.0', '44.0', '20.0', '110.0', '26.0', '40.0', '35.0', '36.0', '12.0', '15.0', '26.0', '20.0', '60.0', '12.0', '25.0', '17.0', '20.0', '9.0', 'nan', '25.0', '37.0', '98.0', '25.0', '26.0', '12.0', '20.0', 'nan', '21.0', '10.0', '15.0', '42.0', '25.0', 'nan', '15.0', '16.0', '30.0', '25.0', '15.0', '28.0', '28.0', '24.0', '25.0', '15.0', '35.0', '18.0', '40.0', '35.0', '35.0', '22.0', '45.0', '65.0', '35.0', '35.0', '38.0', '40.0', '20.0', '34.0', '55.0', '117.0', '40.0', '15.0', '42.0', '68.0', '40.0', '32.0', '60.0', '18.0', '32.0', '20.0', '19.0', '25.0', '75.0', '21.0', '20.0', '52.0', '55.0', '48.0', '80.0', '50.0', '18.0', '35.0', '31.0'],
    'variety': ['Cabernet Sauvignon', 'Tinta de Toro', 'Sauvignon Blanc', 'Pinot Noir', 'Provence red blend', 'Tinta de Toro', 'Tinta de Toro', 'Tinta de Toro', 'Pinot Noir', 'Pinot Noir', 'Friulano', 'Pinot Noir', 'Pinot Noir', 'Tannat', 'Pinot Noir', 'Chardonnay', 'Cabernet Sauvignon', 'Tempranillo', 'Malbec', 'Pinot Noir', 'Rosé', 'Tempranillo Blend', 'Tinta de Toro', 'Chardonnay', 'Pinot Noir', 'Chardonnay', 'Pinot Noir', 'Pinot Noir', 'Pinot Noir', 'Syrah', 'Mavrud', 'Chardonnay', 'Sangiovese', 'Sparkling Blend', 'Chardonnay', 'Sangiovese', 'Rhône-style White Blend', 'Sangiovese', 'Sangiovese', 'Red Blend', 'Mencxada', 'Palomino', 'Petite Sirah', 'Red Blend', 'Syrah', 'Red Blend', 'Sangiovese', 'Cabernet Sauvignon', 'Sangiovese', 'Cabernet Sauvignon', 'Sangiovese', 'Chardonnay', 'Sauvignon Blanc', 'Pinot Noir', 'Chardonnay', 'Cabernet Sauvignon', 'Sauvignon Blanc', 'Riesling', 'Cabernet Sauvignon-Syrah', 'Red Blend', 'Malbec', 'Pinot Noir', 'Malbec', 'Chardonnay', 'Portuguese Red', 'Syrah', 'Chardonnay', 'Cabernet Sauvignon', 'Pinot Noir', 'Cabernet Sauvignon', 'Cabernet Sauvignon', 'Pinot Noir', 'Nebbiolo', 'Pinot Gris', 'Portuguese Red', 'Pinot Noir', 'Chardonnay', 'Sauvignon Blanc', 'Cabernet Sauvignon', 'Nebbiolo', 'Pinot Noir', 'Cabernet Sauvignon', 'Nebbiolo', 'Nebbiolo', 'Nebbiolo', 'Nebbiolo', 'Chardonnay', 'Cabernet Sauvignon', 'Pinot Noir', 'Meritage', 'Cabernet Sauvignon', 'Baga', 'Glera', 'Chardonnay', 'Portuguese Red', 'Malbec-Merlot', 'Chardonnay', 'Cabernet Sauvignon', 'Merlot-Malbec', 'Ugni Blanc-Colombard', 'Viognier', 'Cabernet Sauvignon', 'Sangiovese', 'Cabernet Sauvignon-Cabernet Franc', 'Moscato', 'Pinot Grigio', 'Cabernet Franc', 'Chardonnay', 'White Blend', 'Chardonnay', 'Portuguese Red', 'Rosé', 'Cabernet Sauvignon', 'Riesling', 'Sauvignon Blanc', 'Malbec', 'Monastrell', 'Rosé', 'Gamay', 'Portuguese Red', 'Pinot Noir', 'Pinot Noir', 'Sparkling Blend', 'Chardonnay', 'Pinot Noir', 'Pinot Noir', 'Zinfandel', 'Cabernet Sauvignon', 'Tempranillo', 'White Blend', 'Greco', 'Chardonnay', 'Barbera', 'Chardonnay', 'Cabernet Sauvignon', 'Grenache', 'Zinfandel', 'Rhône-style Red Blend', 'Tempranillo', 'Rosé', 'Rosé', 'Sauvignon Blanc', 'Grenache', 'Chardonnay', 'Albariño', 'Pinot Noir', 'Zinfandel', 'Albariño', 'Syrah', 'Malvasia Bianca', 'Pinot Noir', 'White Blend', 'Sparkling Blend', 'Assyrtiko', 'Malagouzia', 'Carmenère', 'Bordeaux-style Red Blend', 'Sangiovese', 'Tempranillo', 'Red Blend', 'Bordeaux-style Red Blend', 'Pinot Noir', 'Tempranillo Blend', 'Syrah', 'Viognier', 'Pinot Noir', 'Red Blend', 'Red Blend', 'Touriga Nacional', 'Chardonnay', 'Pinot Noir', 'Cabernet Sauvignon-Cabernet Franc', 'Agiorgitiko', 'Pinot Noir', 'Rhône-style Red Blend', 'Tinta de Toro', 'Sangiovese', 'Red Blend', 'Cabernet Sauvignon', 'Red Blend', 'Chardonnay', 'Syrah', 'Pinot Noir', 'Picpoul', 'Bordeaux-style Red Blend', 'Bordeaux-style Red Blend', 'Zinfandel', 'Zinfandel', 'Godello', 'Red Blend', 'Malbec', 'Bordeaux-style Red Blend', 'Bordeaux-style Red Blend', 'Bordeaux-style Red Blend', 'Bordeaux-style Red Blend', 'Bordeaux-style Red Blend', 'Chardonnay', 'Malbec', 'Chardonnay', 'Riesling', 'Riesling', 'Cabernet Franc', 'Bordeaux-style Red Blend', 'Bordeaux-style Red Blend', 'Gewürztraminer', 'Merlot', 'Cabernet Sauvignon', 'Cabernet Franc', 'Grenache', 'Sparkling Blend', 'Portuguese Red', 'Nebbiolo', 'Zinfandel', 'Nebbiolo', 'Riesling', 'Riesling', 'Syrah-Grenache', 'Nebbiolo', 'Riesling', 'Riesling', 'G-S-M', 'Mourvèdre', 'Riesling', 'Zinfandel', 'Nebbiolo', 'Bordeaux-style White Blend', 'Syrah', 'Cabernet Sauvignon', 'Syrah', 'Portuguese Red', 'Cabernet Sauvignon', 'Cabernet Sauvignon', 'Petit Verdot', 'Cabernet Sauvignon', 'Nebbiolo', 'Riesling', 'Riesling', 'Riesling', 'Portuguese Red', 'Nebbiolo', 'Bordeaux-style Red Blend', 'Bordeaux-style White Blend', 'Bordeaux-style White Blend', 'Bordeaux-style Red Blend', 'Bordeaux-style White Blend', 'Chardonnay', 'Pinot Noir', 'Rosé', 'Chardonnay', 'Rhône-style White Blend', 'Merlot', 'Nebbiolo', 'Pinot Noir', 'Pinot Noir', 'Muscat', 'Nebbiolo', 'Sauvignon Blanc', 'Pinot Noir', 'Nebbiolo', 'Tempranillo', 'Tempranillo Blend', 'Chenin Blanc-Chardonnay', 'Cabernet Sauvignon-Merlot', 'Red Blend', 'Nebbiolo', 'Sauvignon Blanc', 'Pinot Grigio', 'Mourvèdre', 'Chardonnay', 'Cabernet Sauvignon', 'Pinot Noir', 'Chardonnay', 'Chardonnay', 'Rhône-style Red Blend', 'Sparkling Blend', 'Pinot Noir', 'Pinot Bianco', 'Alvarinho', 'Portuguese White', 'Pinot Noir', 'Garganega', 'Sauvignon', 'Malbec', 'Bordeaux-style Red Blend', 'Cabernet Sauvignon', 'Syrah', 'Chardonnay', 'Bordeaux-style Red Blend', 'Chardonnay', 'Pinot Noir', 'Pinot Noir', 'Touriga Nacional', 'Pinot Gris', 'Syrah', 'Gros and Petit Manseng', 'Pinot Noir', 'Sauvignon', 'Pinot Grigio', 'Pinot Noir', 'Zinfandel', 'Syrah', 'Riesling', 'Red Blend', 'Riesling', 'Pinot Noir', 'Chardonnay', 'Pinot Noir', 'Pinot Noir', 'Pinot Noir', 'Pinot Noir', 'Pinot Noir', 'Garganega', 'Garganega', 'Cabernet Sauvignon', 'Pinot Noir', 'Cabernet Sauvignon', 'Sparkling Blend', 'Pinot Noir', 'Tannat-Cabernet', 'Syrah', 'Provence red blend', 'Tempranillo Blend', 'Rosé', 'Red Blend', 'Cabernet Sauvignon', 'Provence red blend', 'Cabernet Sauvignon', 'Rosé', 'Malbec', 'Chardonnay', 'Nebbiolo', 'Riesling', 'Cabernet Sauvignon', 'Albariño', 'Sauvignon Blanc', 'Alicante Bouschet', 'Rhône-style White Blend', 'Pinot Noir', 'Syrah', 'Nebbiolo', 'Nebbiolo', 'Cabernet Sauvignon', 'Nebbiolo', 'Pinot Noir', 'Rhône-style Red Blend', 'Aragonês', 'Chardonnay', 'Chardonnay', 'Silvaner', 'Nebbiolo', 'Chardonnay', 'Pinot Noir', 'Chardonnay', 'Portuguese Red', 'Sparkling Blend', 'Cabernet Sauvignon', 'Chardonnay', 'Pinot Noir', 'Nebbiolo', 'Tempranillo', 'Red Blend', 'Ugni Blanc', 'Grüner Veltliner', 'Pinot Noir', 'Pinot Noir', 'Pinot Noir', 'Frappato', 'Lemberger', 'Sylvaner', 'Chasselas', 'Alsace white blend', 'Pinot Gris', 'Pinot Noir', 'Pinot Noir', 'White Blend', 'White Blend', 'Albariño', 'Greco', 'Riesling', 'Cabernet Sauvignon', 'Cabernet Sauvignon', 'Merlot', 'Red Blend', 'Tempranillo', 'Früburgunder', 'Tempranillo', 'Cabernet Sauvignon', 'Cabernet Sauvignon', 'Rhône-style Red Blend', 'Cabernet Sauvignon', 'Chardonnay', 'Cabernet Sauvignon', 'Sangiovese', 'Malbec', 'Bordeaux-style Red Blend', 'Albariño', 'Pinot Noir', 'Sangiovese', 'Sangiovese', 'White Blend', 'Sangiovese', 'Sangiovese', 'Sangiovese', 'White Blend', 'Rhône-style Red Blend', 'Rhône-style Red Blend', 'Cabernet Sauvignon', 'Sauvignon Blanc', 'Chardonnay', 'Chardonnay', 'White Blend', 'Kekfrankos', 'Sangiovese', 'Chardonnay', 'Cabernet Sauvignon', 'Rhône-style Red Blend', 'Tempranillo', 'Sangiovese', 'Red Blend', 'Sangiovese', 'Cabernet Sauvignon', 'Zinfandel', 'Cabernet Franc', 'Grenache', 'Sparkling Blend', 'Tempranillo', 'Sauvignon Blanc', 'Bordeaux-style Red Blend', 'Chardonnay', 'Cabernet Sauvignon', 'Cabernet Sauvignon', 'Rhône-style White Blend', 'Sangiovese', 'Sangiovese', 'Bordeaux-style White Blend', 'Cabernet Sauvignon', 'Chardonnay', 'White Blend', 'Vermentino', 'Sherry', 'Red Blend', 'Riesling', 'Tempranillo', 'Sherry', 'Tempranillo Blend', 'Tempranillo', 'Red Blend', 'Sangiovese', 'Sangiovese', 'Sangiovese', 'Rosé', 'White Blend', 'Chardonnay', 'Syrah', 'Portuguese Red', 'Sauvignon Blanc', 'Moscato', 'Portuguese White', 'Rosé', 'Aglianico', 'Malbec', 'Sauvignon Blanc', 'Cabernet Sauvignon', 'Viognier', 'Merlot', 'Pinot Noir', 'White Blend', 'Malbec', 'Chardonnay', 'Torrontés', 'Sauvignon Blanc', 'Portuguese Red', 'Primitivo', 'Touriga Nacional', 'Pinot Noir', 'Red Blend', 'Semillon-Sauvignon Blanc', 'Barbera', 'Portuguese Red', 'Portuguese Rosé', 'Pinot Noir', 'Agiorgitiko', 'Grenache-Syrah', 'Sangiovese', 'Red Blend', 'White Blend', 'Riesling', 'Prié Blanc', 'Chardonnay', 'Bordeaux-style Red Blend', 'Cabernet Sauvignon', 'Negrette', 'Pinot Noir', 'Pinot Noir', 'Red Blend', 'Syrah', 'Syrah', 'Red Blend', 'Cabernet Sauvignon', 'Red Blend', 'Grenache-Syrah', 'Zinfandel', 'Red Blend', 'Syrah', 'Zinfandel', 'Pinot Noir', 'Albariño', 'Red Blend', 'Tempranillo', 'Sparkling Blend', 'Chardonnay', 'Riesling', 'Portuguese Red', 'Zinfandel', 'Bordeaux-style Red Blend', 'Cabernet Sauvignon', 'Red Blend', 'Riesling', 'Chardonnay', 'Portuguese Red', 'Chardonnay', 'Baga', 'Chardonnay', 'Syrah', 'Chardonnay', 'Riesling', 'Riesling', 'Chardonnay', 'Chardonnay', 'Furmint', 'Nebbiolo', 'Viognier', 'Nebbiolo', 'Bordeaux-style Red Blend', 'Portuguese Red', 'Riesling', 'Chardonnay', 'Bordeaux-style Red Blend', 'Viognier', 'Chardonnay', 'Cabernet Franc', 'Zinfandel', 'Riesling', 'Pinot Noir', 'Pinot Noir', 'Pinot Noir', 'Pinot Noir', 'Riesling', 'Carignane', 'White Blend', 'Chardonnay', 'Sylvaner', 'Pinot Noir', 'White Blend', 'Pinot Blanc', 'Pinot Gris', "Nero d'Avola", 'Zinfandel', 'Moscato', 'Assyrtiko', 'Pinot Noir', 'Chardonnay', 'Frappato', 'Cabernet Sauvignon', 'Tempranillo', 'Tempranillo Blend', 'Merlot', 'Riesling', 'Cabernet Sauvignon', 'Cabernet Sauvignon', 'Pinot Noir', 'Pinot Noir', 'Red Blend', 'Cabernet Sauvignon', 'Chardonnay', 'Chardonnay', 'Friulano', 'Tannat-Cabernet', 'Pinot Noir', 'Pinot Noir', 'Malbec-Merlot', 'Pinot Noir', 'St. Laurent', 'Bordeaux-style Red Blend', 'Cabernet Sauvignon', 'Pinot Noir', 'Tempranillo', 'Blauburgunder', 'Blaufränkisch', 'Syrah', 'Chardonnay', 'Pinot Noir', 'Zinfandel', 'Chardonnay', 'Cabernet Sauvignon', 'Pinot Noir', 'Cabernet Sauvignon', 'Zinfandel', 'Red Blend', 'Provence red blend', 'Zinfandel', 'Chardonnay', 'Cabernet Sauvignon', 'Portuguese White', 'Pinot Grigio', 'Pinot Noir', 'Riesling', 'Riesling', 'Riesling', 'Scheurebe', 'Riesling', 'White Blend', 'Pinot Gris', 'Portuguese Red', 'Chardonnay', 'Pinot Noir', 'Chardonnay', 'Red Blend', 'Pinot Noir', 'Riesling', 'Riesling', 'Riesling', 'Riesling', 'Riesling', 'Riesling', 'Sauvignon Blanc', 'Sauvignon', 'Bordeaux-style Red Blend', 'Portuguese Red', 'Chardonnay', 'Cabernet Sauvignon', 'Pinot Noir', 'Nebbiolo', 'Portuguese Red', 'Nebbiolo', 'Bordeaux-style Red Blend', 'Gewürztraminer', 'Nebbiolo', 'Nebbiolo', 'Nebbiolo', 'Barbera', 'Albariño', 'Pinot Noir', 'Malbec', 'Portuguese White', 'Gewürztraminer', 'Rhône-style White Blend', 'Red Blend', 'Chardonnay', 'Riesling', 'Cabernet Sauvignon', 'Barbera', 'Tempranillo', 'Nebbiolo', 'Pinot Noir', 'Grenache', 'Chardonnay', 'Nebbiolo', 'Nebbiolo', 'Nebbiolo', 'Pinot Noir', 'Sauvignon Blanc', 'Malbec', 'Sauvignon Blanc', 'Meritage', 'Grenache', 'Bordeaux-style Red Blend', 'Chardonnay', 'Sauvignon Blanc', 'Nebbiolo', 'Pinot Noir', 'Gewürztraminer', 'Sauvignon Blanc', 'Pinot Noir', 'Pinot Noir', 'Viognier', 'White Blend', 'Nebbiolo', 'Chardonnay', 'Bordeaux-style White Blend', 'Bordeaux-style White Blend', 'Bordeaux-style White Blend', 'Bordeaux-style White Blend', 'Merlot', 'Bordeaux-style White Blend', 'Pinot Noir', 'Chardonnay', 'Pinot Noir', 'Pinot Noir', 'Tempranillo', 'Cabernet Sauvignon', 'Sparkling Blend', 'Mavrud', 'Chardonnay', 'Pinot Noir', 'Pinot Noir', 'Cabernet Franc', 'Pinot Noir', 'Syrah', 'Sangiovese', 'Chardonnay', 'Sangiovese', 'Sauvignon Blanc', 'Red Blend', 'Chardonnay', 'Riesling', 'Cabernet Franc', 'Sangiovese', 'Zinfandel', 'Sauvignon Blanc', 'Bordeaux-style Red Blend', 'Ribolla Gialla', 'Charbono', 'Sangiovese', 'Pinot Gris', 'Cabernet Sauvignon', 'Palomino', 'Red Blend', 'Tempranillo', 'Rosé', 'Red Blend', 'Sauvignon Blanc', 'Torrontés', 'Malbec-Cabernet Sauvignon', 'Sauvignon Blanc', 'Red Blend', 'Rosé', 'Red Blend', 'Cabernet Sauvignon', 'Pinot Noir-Gamay', 'Pinot Nero', 'Portuguese Red', 'Rosé', 'Malbec', 'Sauvignon Blanc', 'Cabernet Sauvignon', 'Merlot', 'Malbec', 'Garganega', 'White Blend', 'Portuguese Red', 'Chardonnay', 'Bordeaux-style Red Blend', 'Red Blend', 'Sauvignon Blanc', 'Rhône-style Red Blend', 'Sparkling Blend', 'Cabernet Sauvignon', 'Chardonnay', 'Chardonnay', 'Malbec', 'Red Blend', 'Chardonnay', 'Riesling', 'Chardonnay', 'Gros Manseng', 'Tempranillo', 'Red Blend', 'Petit Verdot', 'Red Blend', 'Cabernet Sauvignon', 'G-S-M', 'Pinot Noir', 'Pinot Gris', 'Pinot Noir', 'Red Blend', 'Syrah', 'Pinot Noir', 'Syrah', 'Cabernet Franc', 'Cabernet Sauvignon', 'Riesling', 'Rosé', 'Red Blend', 'Red Blend', 'Portuguese Red', 'Portuguese Red', 'Portuguese Red', 'Sauvignon Blanc', 'White Blend', 'Sangiovese', 'Sangiovese', 'Cabernet Sauvignon', 'Sangiovese', 'Bordeaux-style Red Blend', 'Bordeaux-style Red Blend', 'Bordeaux-style White Blend', 'Bordeaux-style Red Blend', 'Bordeaux-style Red Blend', 'Bordeaux-style Red Blend', 'Bordeaux-style Red Blend', 'Red Blend', 'Primitivo', 'Red Blend', 'Merlot', 'Bordeaux-style Red Blend', 'Syrah', 'Sauvignon Blanc', 'Cabernet Sauvignon', 'Rhône-style White Blend', 'Syrah', 'Red Blend', 'Bordeaux-style Red Blend', 'Pinot Blanc', 'Zinfandel', 'Red Blend', 'Chardonnay', 'Gewürztraminer', 'Cabernet Sauvignon', 'Bordeaux-style Red Blend', 'Moscato', 'Assyrtiko', 'Pinot Noir', 'Chardonnay', 'Frappato', 'Chardonnay', 'Sylvaner', 'Pinot Noir', 'White Blend', 'Pinot Blanc', 'White Blend', 'Pinot Gris', 'Cabernet Sauvignon', 'Riesling', 'Nerello Mascalese', 'Shiraz', 'Merlot', 'Cabernet Sauvignon', 'Negroamaro', 'Mourvèdre', 'Barbera', 'Red Blend', 'Tempranillo', 'Red Blend', 'Tempranillo Blend', 'Rhône-style Red Blend', 'Zinfandel', 'Syrah', 'Riesling', 'Cabernet Franc', 'Cabernet Sauvignon', 'Sparkling Blend', 'Champagne Blend', 'Merlot', 'Sparkling Blend', 'Cabernet Sauvignon', 'Pinot Noir', 'Chardonnay', 'Romorantin', 'Sauvignon Blanc', 'Pinot Noir', 'Syrah', 'Syrah', 'Pinot Noir', 'Sauvignon Blanc', 'Pinot Noir', 'Sangiovese', 'Rosé', 'Godello', 'Palomino', 'Red Blend', 'Tempranillo', 'Sangiovese', 'Red Blend', 'Tempranillo', 'Red Blend', 'Red Blend', 'Sangiovese', 'Red Blend', 'Cabernet Sauvignon', 'Viognier', 'Chardonnay', 'Chardonnay', 'Bordeaux-style Red Blend', 'Nebbiolo', 'Riesling', 'Nebbiolo', 'Nebbiolo', 'Zinfandel', 'Chardonnay', 'Pinot Nero', 'Nebbiolo', 'Portuguese Red', 'Portuguese Red', 'Riesling', 'Riesling', 'Syrah', 'Cabernet Sauvignon', 'Merlot', 'Syrah-Cabernet Sauvignon', 'Cabernet Sauvignon', 'Rhône-style Red Blend', 'Red Blend', 'Riesling', 'Red Blend', 'Cabernet Sauvignon', 'Chardonnay', 'White Blend', 'Red Blend', 'Gewürztraminer', 'Malbec', 'Syrah', 'Chardonnay', 'Tannat-Cabernet', 'Syrah', 'Syrah', 'Chardonnay', 'Rosé', 'Rosé', 'Malbec', 'Rosé', 'Rosé', 'Cabernet Sauvignon', 'Sauvignon Blanc', 'Red Blend', 'Chardonnay', 'Cabernet Sauvignon', 'Syrah', 'Pinot Noir', 'Sherry', 'Pinot Noir', 'Sparkling Blend', 'Tannat-Merlot', 'Syrah', 'Tempranillo', 'Pinot Noir', 'Chardonnay', 'Pinot Noir', 'Pinot Noir', 'Pinot Noir', 'Red Blend', 'Portuguese Red', 'Portuguese Red', 'Portuguese Red', 'Duras', 'Red Blend', 'Sauvignon Blanc', 'White Blend', 'Sauvignon Blanc', 'Chardonnay', 'Garnacha', 'Rhône-style Red Blend', 'Pinot Gris', 'Red Blend', 'Red Blend', 'Sparkling Blend', 'Red Blend', 'Pinot Gris', 'Cabernet Sauvignon', 'Cabernet Sauvignon', 'Tinta Francisca', 'Red Blend', 'Rosé', 'Cabernet Sauvignon', 'Red Blend', 'Red Blend', 'Pinot Noir', 'Portuguese Red', 'Pinot Noir', 'White Blend', 'Nebbiolo', 'Tempranillo', 'Portuguese Red', 'Red Blend', 'Tempranillo Blend', 'Barbera', 'Cabernet Sauvignon', 'Pinot Noir', 'Riesling', 'Pinot Noir', 'Cabernet Sauvignon', 'Nebbiolo', 'Portuguese White', 'Chardonnay', 'Red Blend', 'Chardonnay', 'Pinot Noir', 'Cabernet Sauvignon', 'Nebbiolo', 'Cabernet Sauvignon', 'Nebbiolo', 'Nebbiolo', 'Nebbiolo', 'Nebbiolo', 'Nebbiolo', 'Tempranillo', 'Nebbiolo', 'Pinot Noir', 'Pinot Noir', 'Sparkling Blend', 'Garganega', 'Chardonnay', 'Chardonnay', 'Portuguese White', 'Portuguese White', 'Alicante Bouschet', 'Portuguese Sparkling', 'Sauvignon Blanc', 'White Blend', 'Malbec', 'Portuguese Sparkling', 'Chardonnay', 'Pinot Grigio', 'Portuguese Sparkling', 'Portuguese Red', 'Portuguese Sparkling', 'Chardonnay', 'Malbec', 'Chenin Blanc', 'Rhône-style White Blend', 'Cabernet Sauvignon', 'Sauvignon Blanc', 'Rosé', 'Bordeaux-style White Blend', 'Chardonnay', 'Portuguese Red', 'Portuguese Red', 'White Blend', 'Chardonnay', 'Garganega', 'Riesling', 'Pinot Noir', 'White Blend', 'Pinot Noir', 'Gamay', 'Portuguese Red', 'Portuguese Red', 'Portuguese Red', 'Pinot Noir', 'Syrah', 'Portuguese Red', 'Portuguese Red', 'Riesling', 'Portuguese Red', 'Bordeaux-style Red Blend', 'Gamay', 'Lemberger', 'Red Blend', 'Red Blend', 'Turbiana', 'Pinot Noir', 'Petit Verdot', 'Red Blend', 'Portuguese Red', 'Pinot Noir', 'Portuguese White', 'Petite Verdot', 'Touriga Nacional', 'Portuguese Red', 'Pinot Noir', 'Nebbiolo', 'Nebbiolo', 'Pinot Noir', 'Merlot', 'Pinot Noir', 'Cabernet Franc', 'Bordeaux-style Red Blend', 'Torrontés', 'Bordeaux-style Red Blend', 'Cabernet Franc', 'Portuguese Red', 'Pinot Noir', 'Mourvèdre', 'Nebbiolo', 'Torrontés', 'Mencxada', 'Chardonnay', 'Merlot', 'Posip', 'Zinfandel', 'Bordeaux-style Red Blend', 'Pinot Noir', 'Chardonnay', 'Sauvignon Blanc', 'Fumé Blanc', 'Sauvignon Blanc', 'Nebbiolo', 'Pinot Noir', 'Nebbiolo', 'Pinot Noir', 'Merlot', 'Cabernet Sauvignon', 'Chardonnay', 'Zinfandel', 'Nebbiolo', 'Cabernet Sauvignon', 'Monastrell', 'Bordeaux-style Red Blend', 'Bordeaux-style Red Blend', 'Cabernet Sauvignon', 'Bordeaux-style Red Blend', 'Bordeaux-style Red Blend', 'Bordeaux-style Red Blend', 'Syrah', 'Riesling', 'Chardonnay', 'White Blend', 'Bordeaux-style Red Blend', 'White Blend', 'Riesling', 'Merlot', 'Bordeaux-style Red Blend', 'White Blend', 'Red Blend', 'Roussanne', 'Cabernet Sauvignon', 'Touriga Nacional', 'Cabernet Sauvignon', 'Sangiovese', 'Merlot', 'Tempranillo', 'Sauvignon Blanc', 'Tempranillo Blend', 'Cabernet Sauvignon', 'Mourvèdre', 'Grillo', 'Chardonnay', 'Pinot Noir', 'Pinot Noir', 'Grenache', 'Syrah', 'Riesling', 'Chardonnay', 'Pinot Noir', 'Pinot Noir', 'Müller-Thurgau', 'Pinot Noir', 'Sauvignon Blanc', 'Syrah', 'Cabernet Sauvignon', 'Chardonnay', 'Pinot Gris', 'Gewürztraminer', 'Assyrtiko', 'Pinot Blanc', 'Pinot Auxerrois', 'Pinot Blanc', 'Pinot Noir', 'Cabernet Franc', 'Ribolla Gialla', 'Sangiovese', 'Sangiovese', 'Chardonnay', 'Pinot Noir', 'Chardonnay', 'Chardonnay', 'Petit Verdot', 'Malbec', 'Sangiovese', 'Bordeaux-style Red Blend', 'Port', 'Sauvignon Blanc', 'Pinot Noir', 'Sangiovese', 'Riesling', 'Cabernet Sauvignon', 'Shiraz', 'Red Blend', 'Cabernet Sauvignon', 'Chardonnay', 'Sangiovese', 'Red Blend', 'Tempranillo', 'Red Blend', 'Red Blend', 'Sangiovese', 'Rosé', 'Cabernet Sauvignon', 'Chardonnay', 'Gewürztraminer', 'Syrah', 'Chardonnay', 'Malbec', 'Tannat-Cabernet', 'Pinot Noir', 'Chardonnay', 'Syrah', 'Pinot Noir', 'Pinot Noir', 'Blaufränkisch', 'Cabernet Sauvignon', 'Pinot Noir', 'Malbec', 'Cabernet Blend', 'Sauvignon Blanc', 'Riesling', 'White Blend', 'Chardonnay', 'Pinot Noir', 'Tempranillo', 'Tempranillo Blend', 'Red Blend', 'Rosé', 'Chardonnay', 'Aglianico', 'Grenache', 'Syrah', 'Grüner Veltliner', 'Pinot Noir', 'Pinot Noir', 'Pinot Noir', 'Pinot Gris', 'Riesling', 'Nebbiolo', 'Nebbiolo', 'Cabernet Sauvignon', 'Portuguese Red', 'Gewürztraminer', 'Nebbiolo', 'Pinot Noir', 'Riesling', 'Chardonnay', 'Chardonnay', 'Cabernet Sauvignon', 'Nebbiolo', 'Nebbiolo', 'Nebbiolo', 'Nebbiolo', 'Nebbiolo', 'Cabernet Franc-Cabernet Sauvignon', 'Zinfandel', 'White Blend', 'Champagne Blend', 'Nebbiolo', 'Nebbiolo', 'Cabernet Sauvignon', 'Red Blend', 'Pinot Noir', 'Pinot Noir', 'Rhône-style White Blend', 'Riesling', 'Chardonnay', 'Cabernet Sauvignon', 'Chardonnay', 'Castelão', 'Riesling', 'Riesling', 'Riesling', 'Riesling', 'Riesling', 'Portuguese Red', 'Bordeaux-style Red Blend', 'Bordeaux-style Red Blend', 'Nebbiolo', 'Nebbiolo', 'Syrah', 'Cabernet Sauvignon', 'Cabernet Franc', 'Portuguese Red', 'Bordeaux-style Red Blend', 'Bordeaux-style Red Blend', 'Carmenère', 'Chardonnay', 'Encruzado', 'Cabernet Sauvignon', 'Chardonnay', 'Cabernet Sauvignon', 'Portuguese Red', 'Nebbiolo', 'Bordeaux-style Red Blend', 'Touriga Nacional-Cabernet Sauvignon', 'Chardonnay', 'Sauvignon Blanc', 'Rhône-style White Blend', 'Malbec', 'Chenin Blanc', 'Sangiovese', 'Chardonnay', 'Chardonnay', 'Colombard-Sauvignon Blanc', 'Malbec-Merlot', 'Malbec', 'Sauvignon Blanc', 'Zinfandel', 'Portuguese Red', 'Portuguese White', 'Cabernet Sauvignon', 'Moscatel', 'Chardonnay', 'Malbec', 'Marsanne', 'Red Blend', 'Malbec', 'Portuguese Red', 'Portuguese White', 'Portuguese Red', 'White Blend', 'White Blend', 'Siria', 'Chardonnay', 'Cabernet Sauvignon', 'Bordeaux-style Red Blend', 'Bordeaux-style Red Blend', 'Bordeaux-style Red Blend', 'Syrah', 'Riesling', 'Chardonnay', 'Merlot', 'Sangiovese', 'Blaufränkisch', 'Red Blend', 'Cabernet Sauvignon', 'Monastrell', 'Cabernet Sauvignon', 'Cabernet Franc', 'Malbec', 'Malbec', 'Pinot Noir', 'Red Blend', 'Garnacha Blanca', 'Riesling', 'Red Blend', 'Bordeaux-style Red Blend', 'Bordeaux-style Red Blend', 'Bordeaux-style Red Blend', 'Bordeaux-style Red Blend', 'Bordeaux-style Red Blend', 'Bordeaux-style Red Blend', 'Zinfandel', 'Sauvignon Blanc', 'Garnacha', 'Red Blend', 'Chardonnay', 'Red Blend', 'Portuguese Red', 'Malbec', 'Pinot Noir', 'Red Blend', 'Riesling', 'Red Blend', 'Red Blend', 'Agiorgitiko', 'Sauvignon Blanc', 'Merlot-Cabernet Sauvignon', 'Gros and Petit Manseng', 'Red Blend', 'Pinot Noir', 'Mourvèdre', 'Red Blend', 'Red Blend', 'Port', 'Malbec', 'Pinot Noir', 'Meritage', 'Rosé', 'Bordeaux-style Red Blend', 'Grenache', 'Zinfandel', 'Riesling', 'Sauvignon Blanc', 'Tannat', 'Primitivo', 'Turbiana', 'Syrah', 'Riesling', 'Syrah', 'Rhône-style White Blend', 'Arinto', 'Chardonnay', 'Zinfandel', 'Pinot Noir', 'Chardonnay', 'Pinot Noir', 'Pinot Noir', 'Bordeaux-style Red Blend', 'Viognier', 'Bordeaux-style Red Blend', 'Bordeaux-style Red Blend', 'Rhône-style Red Blend', 'Portuguese Red', 'Chardonnay', 'Bordeaux-style Red Blend', 'Petit Manseng', 'Riesling', 'Portuguese Red', 'Chardonnay', 'Pinot Noir', 'Turbiana', 'Loureiro', 'Portuguese Red', 'Pinot Noir', 'Tempranillo', 'Pinot Gris', 'Cabernet Sauvignon', 'Sauvignon Blanc', 'Cabernet Sauvignon', 'Nebbiolo', 'Pinot Noir', 'Nebbiolo', 'Pinot Noir', 'Sauvignon Blanc', 'Pinot Noir', 'Malbec', 'Pinot Noir', 'Pinot Noir', 'Pinot Noir', 'Melon', 'Pinot Gris', 'Petite Sirah', 'Nebbiolo', 'Grenache-Syrah', 'Mencxada', 'Viognier', 'Pinot Gris', 'Red Blend', 'Pinot Noir', 'Moscatel', 'Nebbiolo', 'Pinot Gris', 'Pinot Noir', 'Carricante', 'Pinot Noir', 'White Blend', 'Cabernet Sauvignon', 'Syrah', 'Fiano', 'Rhône-style Red Blend', 'Assyrtiko', 'Zinfandel', 'Pinot Noir', 'Cabernet Sauvignon', 'Zinfandel', 'Chardonnay', 'Rosé', 'Sylvaner', 'Red Blend', 'Grenache', 'Silvaner', 'Pinot Noir', 'Sylvaner', 'Pinot Noir', 'Petite Sirah', 'Zinfandel', 'Red Blend', 'Zinfandel', 'Tempranillo Blend', 'Tempranillo Blend', 'Zinfandel', 'Schwartzriesling', 'Garnacha', 'Red Blend', 'Sangiovese', 'Merlot', 'Chardonnay', 'Sangiovese', 'Rhône-style Red Blend', 'Sauvignon Blanc', 'Champagne Blend', 'Sangiovese-Syrah', 'Vermentino', 'White Blend', 'Rosé', 'Pinot Noir', 'Red Blend', 'Red Blend', 'Chardonnay', 'Pinot Noir', 'Cabernet Sauvignon', 'Cabernet Sauvignon', 'Cabernet Franc', 'Red Blend', 'Red Blend', 'Red Blend', 'Cabernet Sauvignon', 'Pinot Noir', 'Chardonnay', 'Rosé', 'Red Blend', 'Syrah', 'Furmint', 'Sparkling Blend', 'Pinot Noir', 'Pinot Gris', 'Riesling', 'Nebbiolo', 'Nebbiolo', 'Cabernet Sauvignon', 'Malbec', 'Pinot Gris', 'Nebbiolo', 'Malbec', 'Nebbiolo', 'Zinfandel', 'Barbera', 'Bordeaux-style White Blend', 'Melon', 'Malbec-Merlot', 'Bordeaux-style Red Blend', 'Tannat-Cabernet Franc', 'Rhône-style Red Blend', 'Pinot Noir', 'Nebbiolo', 'Chardonnay', 'Pinot Blanc', 'Nebbiolo', 'Cabernet Sauvignon', 'Mencxada', 'Portuguese Red', 'Cabernet Sauvignon', 'Sauvignon Blanc', 'Sauvignon Blanc', 'Grenache', 'Chardonnay', 'Pinot Noir', 'Gros Manseng', 'Rosé', 'Rosé', 'Tannat', 'Pinot Noir', 'Pinot Noir', 'Cabernet Sauvignon', 'Grüner Veltliner', 'Grenache', 'Grüner Veltliner', 'Pinot Gris', 'Pinot Noir', 'Pinot Noir', 'Tempranillo', 'Pinot Noir', 'Rosé', 'Red Blend', 'White Blend', 'Sparkling Blend', 'Barbera', 'Petite Sirah', 'Chardonnay', 'Cabernet Franc-Merlot', 'Syrah', 'Zinfandel', 'Zinfandel', 'Portuguese Red', 'Portuguese White', 'Portuguese Red', 'White Blend', 'Sangiovese', 'Bordeaux-style Red Blend', 'Torrontés', 'Malbec', 'Malbec', 'Rosé', 'Sauvignon Blanc', 'Sauvignon Blanc-Semillon', 'Alvarinho', 'Portuguese White', 'Rhône-style White Blend', 'Bordeaux-style Red Blend', 'Red Blend', 'Pinot Noir', 'Portuguese Sparkling', 'White Blend', 'Bordeaux-style White Blend', 'Sauvignon Blanc', 'Chenin Blanc', 'Pinot Noir', 'Chenin Blanc', 'Malbec', 'Chenin Blanc', 'Macabeo', 'Rosé', 'Portuguese White', 'Syrah', 'Chardonnay', 'Bordeaux-style Red Blend', 'Merlot', 'Portuguese Red', 'Syrah', 'Sauvignon Blanc', 'Alfrocheiro', 'Zinfandel', 'Merlot', 'Syrah', 'Riesling', 'Pinot Blanc', 'Gewürztraminer', 'Syrah', 'Chardonnay', 'Cabernet Sauvignon', 'Tempranillo', 'Red Blend', 'Syrah', 'Portuguese Red', 'Chardonnay', 'Bordeaux-style White Blend', 'Chardonnay', 'Sangiovese', 'Cabernet Sauvignon', 'Portuguese Red', 'Chardonnay', 'Portuguese Red', 'Riesling', 'Chardonnay', 'Sauvignon Blanc', 'Zinfandel', 'Rhône-style Red Blend', 'White Blend', 'Chardonnay', 'Malbec', 'Aligoté', 'Sangiovese', 'Sangiovese', 'Red Blend', 'Sangiovese', 'Sangiovese', 'Sangiovese', 'Chardonnay', 'Torrontés', 'Red Blend', 'White Blend', 'Bordeaux-style Red Blend', 'Verdejo', 'Sparkling Blend', 'Merlot', 'White Blend', 'Zinfandel', 'Gewürztraminer', 'Red Blend', 'Riesling', 'Syrah', 'Grenache Blanc', 'Chardonnay', 'Champagne Blend', 'Malbec', 'Champagne Blend', 'Red Blend', 'Cabernet Sauvignon', 'Merlot', 'Pinot Noir', 'Pinot Noir', 'Zinfandel', 'Chardonnay', 'Pinot Noir', 'Pinot Noir', 'Red Blend', 'Champagne Blend', 'Bordeaux-style Red Blend', 'Bordeaux-style Red Blend', 'Bordeaux-style Red Blend', 'Turbiana', 'Turbiana', 'Cabernet Sauvignon', 'Portuguese White', 'Portuguese Red', 'Red Blend', 'Fernão Pires', 'Rhône-style Red Blend', 'Chardonnay', 'Riesling', 'Riesling', 'Riesling', 'Spätburgunder', 'Riesling', 'Mourvèdre', 'Red Blend', 'Sparkling Blend', 'Pinot Noir', 'Chardonnay', 'Merlot', 'Red Blend', 'Red Blend', 'Portuguese White', 'Pinot Noir', 'Rosé', 'Merlot', 'Grüner Veltliner', 'Bordeaux-style Red Blend', 'Merlot', 'Chardonnay', 'Red Blend', 'Bordeaux-style White Blend', 'Red Blend', 'Ciliegiolo', 'Cabernet Sauvignon-Carmenère', 'Pinot Noir', 'Merlot', 'Red Blend', 'Red Blend', 'Cabernet Franc', 'Rhône-style Red Blend', 'Pinot Gris', 'Tempranillo', 'Cabernet Sauvignon', 'Portuguese Red', 'Pinot Noir', 'Portuguese Red', 'Zinfandel', 'Merlot', 'Posip', 'Merlot', 'Sauvignon Blanc', 'Sauvignon Blanc', 'Petite Sirah', 'Pinot Noir', 'Sauvignon Blanc', 'Rhône-style White Blend', 'Portuguese White', 'Rosé', 'Chenin Blanc', 'Bordeaux-style Red Blend', 'Sauvignon Blanc', 'Torrontés', 'Pinot Noir', 'Viognier', 'Nebbiolo', 'Tempranillo', 'Tempranillo Blend', 'Red Blend', 'Tempranillo Blend', 'Tempranillo Blend', 'Chenin Blanc', 'Rosé', 'Zinfandel', 'Schwartzriesling', 'Carmenère', 'Chardonnay', 'Sauvignon Blanc', 'Pinot Noir', 'Zinfandel', 'Chardonnay', 'Sauvignon Blanc', 'Cabernet Franc', 'Sparkling Blend', 'Zinfandel', 'Pinot Noir', 'Zinfandel', 'Rhône-style Red Blend', 'Riesling', 'Syrah', 'Pinot Noir', 'Chardonnay', 'Pinot Noir', 'Rosé', 'Grenache', 'Pinot Noir', 'Chardonnay', 'White Blend', 'Pinot Noir', 'Pinot Noir', 'Auxerrois', 'Pinot Noir', 'Pinot Blanc', 'Furmint', 'Syrah', 'Cabernet Franc', 'Sauvignon Blanc', 'Pinot Noir', 'Pinot Noir', 'Zinfandel', 'Sangiovese', 'Red Blend', 'Syrah', 'Zinfandel', 'Red Blend']
})

WINE_DF['country'] = WINE_DF['country'].astype(str)
WINE_DF['province'] = WINE_DF['province'].astype(str)
WINE_DF['points'] = WINE_DF['points'].astype(int)
WINE_DF['price'] = WINE_DF['price'].astype(float)
WINE_DF['variety'] =WINE_DF['variety'].astype(str)

