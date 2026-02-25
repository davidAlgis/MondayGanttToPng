import argparse
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

    # Load data
    tasks = []
    with open(input_path, "r", encoding="utf-8") as f:
        import csv

        reader = csv.reader(f)
        for row in reader:
            if len(row) < 3:
                continue
            start = parse_fr_date(row[1])
            end = parse_fr_date(row[2])
            if start and end:
                tasks.append({"Task": row[0], "Start": start, "End": end})

    if not tasks:
        print("No valid tasks found.")
        return

    df = pd.DataFrame(tasks)
    df = df.iloc[::-1]  # Reverse to show first task at the top

    # Create Plot
    fig, ax = plt.subplots(figsize=(12, 6))

    for i, task in enumerate(df.itertuples()):
        duration = (task.End - task.Start).days
        ax.barh(
            task.Task,
            duration,
            left=task.Start,
            color="#3399FF",
            edgecolor="black",
        )
        # Label inside/near the bar
        ax.text(
            task.Start,
            i,
            f" {task.Task}",
            va="center",
            color="black",
            fontweight="bold",
        )

    # Formatting
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.xticks(rotation=45)
    plt.grid(axis="x", linestyle="--", alpha=0.7)
    plt.tight_layout()

    # Save
    plt.savefig(output_path, dpi=300)
    print(f"Generated PNG: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output")
    args = parser.parse_args()
    generate_png(args.input, args.output)
