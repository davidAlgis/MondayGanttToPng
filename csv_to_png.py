import argparse
import csv
import os
from datetime import datetime, timedelta

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

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


def parse_date(date_str):
    if not date_str:
        return None
    date_str = str(date_str).strip()

    # 1. Handle Excel numeric serial dates
    try:
        val = float(date_str)
        return datetime(1899, 12, 30) + timedelta(days=val)
    except ValueError:
        pass

    # 2. Handle string dates (French/English fallback)
    s = date_str.lower()
    for fr, en in FR_MONTHS.items():
        if fr in s:
            s = s.replace(fr, en)

    formats = [
        "%d-%b-%Y",
        "%d-%b-%y",
        "%d/%m/%Y",
        "%d/%m/%y",
        "%Y-%m-%d",
        "%d-%m-%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def generate_png(input_path, output_path):
    if not output_path:
        output_path = os.path.splitext(input_path)[0] + ".png"

    with open(input_path, "r", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    if not rows:
        print("No data found in CSV.")
        return

    # Fallback default configuration
    task_idx = 0
    start_idx = 1
    end_idx = 2

    # Robust Auto-detection of Column Headers
    for row in rows[:8]:
        row_lower = [str(cell).lower().strip() for cell in row]

        t_idx = -1
        for kw in [
            "task",
            "tâche",
            "tache",
            "name",
            "nom",
            "item",
            "titre",
            "title",
        ]:
            for idx, cell in enumerate(row_lower):
                if kw in cell:
                    t_idx = idx
                    break
            if t_idx != -1:
                break

        s_idx = -1
        for kw in ["start", "début", "debut", "planifié"]:
            for idx, cell in enumerate(row_lower):
                if kw in cell:
                    s_idx = idx
                    break
            if s_idx != -1:
                break

        e_idx = -1
        for kw in ["end", "fin", "échéance", "echeance", "limite"]:
            for idx, cell in enumerate(row_lower):
                if kw in cell:
                    e_idx = idx
                    break
            if e_idx != -1:
                break

        if s_idx != -1 and e_idx != -1:
            task_idx = t_idx if t_idx != -1 else 0
            start_idx = s_idx
            end_idx = e_idx
            print(
                f"Auto-detected -> Task: col {task_idx}, Start: col {start_idx}, End: col {end_idx}"
            )
            break

    tasks = []
    for row in rows:
        if max(task_idx, start_idx, end_idx) >= len(row):
            continue

        start = parse_date(row[start_idx])
        end = parse_date(row[end_idx])
        task_name = row[task_idx].strip()

        if start and end and task_name:
            if any(
                kw in task_name.lower()
                for kw in ["task", "tâche", "tache", "nom", "item"]
            ):
                continue

            # NEW: Smart year display logic for the sub-label column
            if start.year == end.year:
                interval = (
                    f"{start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}"
                )
            else:
                interval = f"{start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')}"

            tasks.append(
                {
                    "Task": task_name,
                    "Start": start,
                    "End": end,
                    "Interval": interval,
                }
            )

    if not tasks:
        print("No valid tasks found after processing row contents.")
        return

    df = pd.DataFrame(tasks).iloc[::-1].reset_index(drop=True)

    MONDAY_GREEN = "#6AB547"
    TEXT_MAIN = "#333333"
    TEXT_SUB = "#888888"
    GRID_COLOR = "#F4F4F4"

    fig, ax = plt.subplots(figsize=(18, 10), facecolor="white")
    min_date = df["Start"].min()
    max_date = df["End"].max()

    for i, task in enumerate(df.itertuples()):
        # A one-day task has Start == End: a zero-length line is not drawn,
        # so give the bar a minimal one-day width (rendered as a round dot).
        bar_end = max(task.End, task.Start + timedelta(days=1))
        ax.plot(
            [task.Start, bar_end],
            [i, i],
            color=MONDAY_GREEN,
            linewidth=26,
            solid_capstyle="round",
            zorder=3,
            clip_on=False,
        )

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

    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))

    plt.xticks(rotation=45, ha="right", color=TEXT_SUB, fontsize=11)
    ax.grid(axis="x", color=GRID_COLOR, linestyle="-", linewidth=1.5, zorder=1)
    ax.set_yticks([])

    for spine in ["left", "top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#CCCCCC")

    # Small padding so bars at the edges (e.g. a one-day task) aren't clipped
    pad = max((max_date - min_date) * 0.01, timedelta(days=2))
    ax.set_xlim(min_date - pad, max_date + pad)
    plt.margins(y=0.1)
    plt.subplots_adjust(left=0.4, bottom=0.2, right=0.95)

    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Successfully generated: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input")
    parser.add_argument("-o", "--output")
    args = parser.parse_args()
    generate_png(args.input, args.output)
