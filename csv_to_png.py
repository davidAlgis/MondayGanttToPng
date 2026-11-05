import argparse
import csv
import os
from datetime import datetime, timedelta

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta

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


def generate_png(input_path, output_path, t0=None):
    """Render the Gantt PNG. If t0 (datetime) is given, dates are replaced by
    offsets relative to T0 (blind planning)."""
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

            # Smart year display logic for the sub-label column
            # (no sub-label in blind mode: dates are hidden)
            if t0 is not None:
                interval = None
            elif start.year == end.year:
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
                    # Working days (Mon-Fri), start and end days included
                    "WorkDays": int(
                        np.busday_count(
                            start.date(), (end + timedelta(days=1)).date()
                        )
                    ),
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

    # X values are plain numbers: days since T0 (blind mode) or matplotlib
    # date numbers (calendar mode).
    if t0 is not None:
        to_x = lambda d: (d - t0).days
    else:
        to_x = mdates.date2num
    df["X0"] = df["Start"].map(to_x)
    df["X1"] = df["End"].map(to_x)
    min_x = df["X0"].min()
    max_x = df["X1"].max()

    for i, task in enumerate(df.itertuples()):
        # A one-day task has Start == End: a zero-length line is not drawn,
        # so give the bar a minimal one-day width (rendered as a round dot).
        bar_end = max(task.X1, task.X0 + 1)
        ax.plot(
            [task.X0, bar_end],
            [i, i],
            color=MONDAY_GREEN,
            linewidth=26,
            solid_capstyle="round",
            zorder=3,
            clip_on=False,
        )

        ax.text(
            (task.X0 + bar_end) / 2,
            i,
            f"{task.WorkDays} j",
            va="center",
            ha="center",
            fontsize=11,
            fontweight="bold",
            color="white",
            zorder=4,
        )

        ax.text(
            -0.02,
            i if t0 is not None else i + 0.12,
            task.Task,
            va="center" if t0 is not None else "bottom",
            ha="right",
            fontsize=12,
            fontweight="bold",
            color=TEXT_MAIN,
            transform=ax.get_yaxis_transform(),
        )

        if task.Interval:
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

    if t0 is not None:
        # One tick per calendar month counted from T0 (T0 + 1 m = same day
        # of the next month).
        margin = max((max_x - min_x) * 0.01, 2)
        ticks, labels = [], []
        for n in range(-240, 241):
            pos = (t0 + relativedelta(months=n) - t0).days
            if min_x - margin <= pos <= max_x + margin:
                ticks.append(pos)
                labels.append(
                    "T0" if n == 0 else f"T0 {'+' if n > 0 else '-'} {abs(n)} m"
                )
        ax.set_xticks(ticks)
        ax.set_xticklabels(labels)
    else:
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))

    plt.xticks(rotation=45, ha="right", color=TEXT_SUB, fontsize=11)
    ax.grid(axis="x", color=GRID_COLOR, linestyle="-", linewidth=1.5, zorder=1)
    ax.set_yticks([])

    for spine in ["left", "top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#CCCCCC")

    # Small padding so bars at the edges (e.g. a one-day task) aren't clipped
    pad = max((max_x - min_x) * 0.01, 2)
    ax.set_xlim(min_x - pad, max_x + pad)
    plt.margins(y=0.1)
    plt.subplots_adjust(left=0.4, bottom=0.2, right=0.95)

    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Successfully generated: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input")
    parser.add_argument("-o", "--output")
    parser.add_argument(
        "--t0",
        help="Reference date T0: show offsets relative to T0 instead of dates",
    )
    args = parser.parse_args()
    t0 = parse_date(args.t0) if args.t0 else None
    if args.t0 and t0 is None:
        parser.error(f"Cannot parse --t0 date: {args.t0}")
    generate_png(args.input, args.output, t0)
