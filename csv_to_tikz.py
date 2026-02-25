import argparse
import csv
import os
from datetime import datetime

# Dictionary to map French month abbreviations to English/Numbers
FR_MONTHS = {
    "janv.": "01",
    "févr.": "02",
    "mars": "03",
    "avr.": "04",
    "mai": "05",
    "juin": "06",
    "juil.": "07",
    "août": "08",
    "sept.": "09",
    "oct.": "10",
    "nov.": "11",
    "déc.": "12",
}


def parse_monday_date(date_str):
    """Converts '05-janv.-2026' to a datetime object."""
    if not date_str or not isinstance(date_str, str):
        return None
    try:
        parts = date_str.split("-")
        if len(parts) != 3:
            return None
        day = parts[0]
        month = FR_MONTHS.get(parts[1].lower(), "01")
        year = parts[2]
        return datetime.strptime(f"{day}-{month}-{year}", "%d-%m-%Y")
    except Exception:
        return None


def generate_tikz(input_path, output_path):
    tasks = []

    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            # Skip empty rows or rows that don't have enough columns
            if len(row) < 3:
                continue

            task_name = row[0].strip()
            start_date = parse_monday_date(row[1])
            end_date = parse_monday_date(row[2])

            # Only keep rows that have valid start and end dates
            if start_date and end_date:
                tasks.append(
                    {"name": task_name, "start": start_date, "end": end_date}
                )

    if not tasks:
        print("No valid tasks found in the CSV.")
        return

    # Determine global start and end to scale the gantt chart
    global_start = min(t["start"] for t in tasks)

    # Helper to calculate "Month Index" relative to the start
    def get_month_index(dt):
        return (
            (dt.year - global_start.year) * 12
            + (dt.month - global_start.month)
            + 1
        )

    tikz_content = [
        "\\begin{tikzpicture}",
        "  \\begin{ganttchart}[",
        "    hgrid,",
        "    vgrid,",
        "    x unit=0.8cm,",
        "    y unit chart=0.7cm,",
        "    time slot format=isodate",
        "  ]{"
        + global_start.strftime("%Y-%m-%d")
        + "}{"
        + max(t["end"] for t in tasks).strftime("%Y-%m-%d")
        + "}",
        "    \\gantttitlecalendar{year, month} \\\\",
    ]

    for t in tasks:
        s = t["start"].strftime("%Y-%m-%d")
        e = t["end"].strftime("%Y-%m-%d")
        # Sanitize task name for LaTeX (escapes & and _)
        clean_name = t["name"].replace("_", "\\_").replace("&", "\\&")
        tikz_content.append(
            f"    \\ganttbar{{{clean_name}}}{{{s}}}{{{e}}} \\\\"
        )

    tikz_content.append("  \\end{ganttchart}")
    tikz_content.append("\\end{tikzpicture}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(tikz_content))

    print(f"TikZ file generated: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert Monday.com CSV to pgfgantt TikZ."
    )
    parser.add_argument("-i", "--input", required=True, help="Input CSV file")
    parser.add_argument("-o", "--output", help="Output .tikz file")

    args = parser.parse_args()

    out = (
        args.output
        if args.output
        else os.path.splitext(args.input)[0] + ".tikz"
    )
    generate_tikz(args.input, out)
