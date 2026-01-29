#! /usr/bin/env python3
"""
Example of a measurement system analysis.

The data file can be:
    .csv | .CSV | .odd.| .ODS | .xlsx | .XLSX | .xlsm | .XLSM | .feather

The data file should be as follows.

There is no sample ID column. One column is the Operator. One column is the
Part. The other two or more columns are the repeated measure for each
Operator by Part; these could be named Y1, Y2, etc. The first row contains the
labels for the columns.

Execute the script in a terminal:
 ./msa.py -pf msa.csv -op Operator -pn Part -dc Y1 Y2
 ./msa.py -pf msa.csv
"""

from pathlib import Path
from os import chdir
import argparse
import time

import dawgdad.control_charts as cc
import matplotlib.pyplot as plt
import dawgdad as dd
import pandas as pd


def main():
    chdir(Path(__file__).parent.resolve())  # required for cron
    parser = argparse.ArgumentParser(
        prog="msa.py",
        description="Create a measurement system analysis."
    )
    parser.add_argument(
        "-pf",
        "--path_or_file",
        type=Path,
        required=True,
        help="Provide a path or file name for data file (required)",
    )
    parser.add_argument(
        "-op",
        "--operator_column",
        default="Operator",
        type=str,
        required=False,
        help="Provide a string for operator column label (default: Operator)",
    )
    parser.add_argument(
        "-pn",
        "--part_column",
        default="Part",
        type=str,
        required=False,
        help="Provide a string for part number column label (default: Part)",
    )
    parser.add_argument(
        "-dc",
        "--data_columns",
        nargs="+",
        default=["Y1", "Y2"],
        type=str,
        required=False,
        help="Provide a string for data column labels (default: Y1 Y2)",
    )
    args = parser.parse_args()
    HEADER_TITLE = "Measurement System Analysis"
    OUTPUT_URL = "msa.html"
    HEADER_ID = "xbar-r-example"
    start_time = time.time()
    original_stdout = dd.html_begin(
        output_url=OUTPUT_URL,
        header_title=HEADER_TITLE,
        header_id=HEADER_ID
    )
    dd.style_graph()
    # df = create_data()
    # allcols = ['Operator', 'Part', 'Y1', 'Y2']
    allcols = [col for col in [args.operator_column, args.part_column] if col]
    allcols.extend(args.data_columns)
    df_all = dd.read_file(
        file_name=args.path_or_file,
        usecols=allcols
    )
    df_data = df_all[args.data_columns]
    print("path or file:", args.path_or_file)
    print("<h2>DataFrame</h2>")
    print(df_all)
    print(df_data)
    print(allcols)
    print(args.data_columns)
    # dd.page_break()
    # xbar_chart(df=data)
    # dd.page_break()
    # r_chart(df=data)
    stop_time = time.time()
    # dd.page_break()
    dd.report_summary(
        start_time=start_time,
        stop_time=stop_time
    )
    dd.html_end(
        original_stdout=original_stdout,
        output_url=OUTPUT_URL
    )


def create_data() -> pd.DataFrame:
    """
    Create a dataframe.
    This function is for demonstration purposes.
    """
    df = pd.DataFrame(
        {
            "Operator": [
                         1, 1, 1, 1, 1,
                         2, 2, 2, 2, 2,
                         3, 3, 3, 3, 3
                        ],
            "Part":     [
                         1, 2, 3, 4, 5,
                         1, 2, 3, 4, 5,
                         1, 2, 3, 4, 5
                        ],
            "Y1":       [
                         667, 648, 857, 559, 654,
                         660, 635, 841, 552, 664,
                         660, 657, 851, 555, 654
                        ],
            "Y2":       [
                         673, 648, 851, 572, 669,
                         664, 638, 851, 556, 648,
                         654, 657, 851, 565, 654
                        ]
        }
    )
    return df


def xbar_chart(
    *,
    df: pd.DataFrame,
    figsize: tuple[float, float] = (8, 6),
    colour: str = "#33bbee",
    xbar_chart_title: str = "Average Control Chart",
    xbar_chart_ylabel: str = "Measurement Xbar (units)",
    xbar_chart_xlabel: str = "Sample",
    graph_file_prefix: str = "xbar_r_example"
) -> None:
    """
    Creates an Xbar control chart.
    Identifies out-of-control points.
    Addd.chart and axis titles.
    Saves the figure in svg format.
    """
    fig = plt.figure(figsize=figsize)
    xbar = cc.Xbar(data=df)
    ax = xbar.ax(fig=fig)
    ax.axhline(
        y=xbar.sigmas[+1],
        linestyle="--",
        dashes=(5, 5),
        color=colour,
        alpha=0.5
    )
    ax.axhline(
        y=xbar.sigmas[-1],
        linestyle="--",
        dashes=(5, 5),
        color=colour,
        alpha=0.5
    )
    ax.axhline(
        y=xbar.sigmas[+2],
        linestyle="--",
        dashes=(5, 5),
        color=colour,
        alpha=0.5
    )
    ax.axhline(
        y=xbar.sigmas[-2],
        linestyle="--",
        dashes=(5, 5),
        color=colour,
        alpha=0.5
    )
    cc.draw_rule(
        xbar,
        ax,
        *cc.points_one(xbar),
        "1"
    )
    cc.draw_rule(
        xbar,
        ax,
        *cc.points_four(xbar),
        "4"
    )
    cc.draw_rule(
        xbar,
        ax,
        *cc.points_two(xbar),
        "2"
    )
    cc.draw_rules(
        cc=xbar,
        ax=ax
    )
    ax.set_title(label=xbar_chart_title)
    ax.set_ylabel(ylabel=xbar_chart_ylabel)
    ax.set_xlabel(xlabel=xbar_chart_xlabel)
    fig.savefig(fname=f"{graph_file_prefix}_xbar.svg")
    dd.html_figure(file_name=f"{graph_file_prefix}_xbar.svg")
    print(
        f"Xbar Report\n"
        f"===================\n"
        f"UCL        : {xbar.ucl.round(3)}\n"
        f"Xbarbar    : {xbar.mean.round(3)}\n"
        f"LCL        : {xbar.lcl.round(3)}\n"
        f"Sigma(Xbar): {xbar.sigma.round(3)}\n"
    )


def r_chart(
    *,
    df: pd.DataFrame,
    figsize: tuple[float, float] = (8, 6),
    colour: str = "#33bbee",
    r_chart_title: str = "Range Control Chart",
    r_chart_ylabel: str = "Measurement R (units)",
    r_chart_xlabel: str = "Sample",
    graph_file_prefix: str = "xbar_r_example"
) -> None:
    """
    Creates an R control chart.
    Identifies out-of-control points.
    Addd.chart and axis titles.
    Saves the figure in svg format.
    """
    fig = plt.figure(figsize=figsize)
    r = cc.R(data=df)
    ax = r.ax(fig=fig)
    ax.axhline(
        y=r.sigmas[+1],
        linestyle="--",
        dashes=(5, 5),
        color=colour,
        alpha=0.5
    )
    ax.axhline(
        y=r.sigmas[-1],
        linestyle="--",
        dashes=(5, 5),
        color=colour,
        alpha=0.5
    )
    ax.axhline(
        y=r.sigmas[+2],
        linestyle="--",
        dashes=(5, 5),
        color=colour,
        alpha=0.5
    )
    ax.axhline(
        y=r.sigmas[-2],
        linestyle="--",
        dashes=(5, 5),
        color=colour,
        alpha=0.5
    )
    cc.draw_rule(
        r,
        ax,
        *cc.points_one(r),
        "1"
    )
    ax.set_title(label=r_chart_title)
    ax.set_ylabel(ylabel=r_chart_ylabel)
    ax.set_xlabel(xlabel=r_chart_xlabel)
    fig.savefig(fname=f"{graph_file_prefix}_r.svg")
    dd.html_figure(file_name=f"{graph_file_prefix}_r.svg")
    print(
        f"R Report\n"
        f"===================\n"
        f"UCL        : {r.ucl.round(3)}\n"
        f"Rbar       : {r.mean.round(3)}\n"
        f"LCL        : {round(r.lcl, 3)}\n"
        f"Sigma(Xbar): {r.sigma.round(3)}\n"
    )


if __name__ == "__main__":
    main()
