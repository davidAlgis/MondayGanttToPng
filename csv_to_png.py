import argparse
import csv
import os
from datetime import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

# Map French months to English for parsing
FR_MONTHS = {
    "janv.": "Jan",
    "févr.": "Feb",
    "mars": "Mar",
    "avr.": "Apr",
    "mai": "May",
    "juin": "Jun",
    "juil.": "Jul",
    "août": "Aug",
    "sept.": "Sep",
    "oct.": "Oct",
    "nov.": "Nov",
    "déc.": "Dec",
}


def parse_fr_date(date_str):
    try:
        for fr, en in FR_MONTHS.items():
            if fr in date_str.lower():
                date_str = date_str.lower().replace(fr, en)
        return datetime.strptime(date_str, "%d-%b-%Y")
    except:
        return None


def generate_png(input_path, output_path):
    if not output_path:
        output_path = os.path.splitext(input_path)[0] + ".png"

    tasks = []
    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 3:
                continue
            start = parse_fr_date(row[1])
            end = parse_fr_date(row[2])
            if start and end:
                # Format: "Jan 05 - Feb 27"
                interval = f"{row[1].split('-')[1]} {row[1].split('-')[0]} - {row[2].split('-')[1]} {row[2].split('-')[0]}"
                tasks.append(
                    {
                        "Task": row[0],
                        "Start": start,
                        "End": end,
                        "Interval": interval,
                    }
                )

    if not tasks:
        print("No valid tasks found.")
        return

    df = pd.DataFrame(tasks).iloc[::-1].reset_index(drop=True)

    # UI Constants
    MONDAY_GREEN = "#6AB547"
    TEXT_MAIN = "#333333"
    TEXT_SUB = "#888888"
    GRID_COLOR = "#F4F4F4"

    # Larger figure size for clarity
    fig, ax = plt.subplots(figsize=(18, 10), facecolor="white")

    # Calculate global date range for the axis
    min_date = df["Start"].min()
    max_date = df["End"].max()

    for i, task in enumerate(df.itertuples()):
        # Draw the pill-shaped bar
        ax.plot(
            [task.Start, task.End],
            [i, i],
            color=MONDAY_GREEN,
            linewidth=26,
            solid_capstyle="round",
            zorder=3,
        )

        # Labels - Positioned to the left of the start of the chart
        # We use transform=ax.get_yaxis_transform() so X is in "axis fraction"
        # but Y is in "data coordinates". -0.02 means 2% to the left of the axis.
        ax.text(
            -0.02,
            i + 0.12,
            task.Task,
            va="bottom",
            ha="right",
            fontsize=12,
            fontweight="bold",
            color=TEXT_MAIN,
            transform=ax.get_yaxis_transform(),
        )

        ax.text(
            -0.02,
            i - 0.12,
            task.Interval,
            va="top",
            ha="right",
            fontsize=10,
            color=TEXT_SUB,
            transform=ax.get_yaxis_transform(),
        )

    # X-Axis Timeline Formatting
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))

    # Style the ticks
    plt.xticks(rotation=45, ha="right", color=TEXT_SUB, fontsize=11)

    # Grid and Aesthetic styling
    ax.grid(axis="x", color=GRID_COLOR, linestyle="-", linewidth=1.5, zorder=1)
    ax.set_yticks([])

    # Hide top/right/left borders
    for spine in ["left", "top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#CCCCCC")

    # Set the visible data range
    ax.set_xlim(min_date, max_date)

    # Final Layout Tweaks
    plt.margins(y=0.1)

    # subplots_adjust + bbox_inches='tight' is the magic combo
    plt.subplots_adjust(left=0.4, bottom=0.2, right=0.95)

    # Save with 'tight' to ensure no text is cut off
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Successfully generated: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output")
    args = parser.parse_args()
    generate_png(args.input, args.output)
