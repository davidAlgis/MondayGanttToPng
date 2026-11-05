# Monday Gantt to PNG

This Python scripts allows you to convert a Monday.com Gantt chart export (`.xlsx`) directly into a modern, sleek PNG image. 


## Installation

Before running the script, ensure you have the required Python libraries installed:

```bash
pip install -r "requirements.txt"

```

## Usage

```bash
python main.py -i "path/to/your/gantt_export.xlsx" -o "output_chart.png"

```

The tool will:

1. Extract the data into a temporary CSV file.
2. Render the PNG with task names and date intervals on the left, and the number of working days (Mon-Fri, start and end included, e.g. `3 j`) in the center of each bar.
3. Automatically clean up any temporary files.

## Options

* `-i`, `--input` <file>: Specify the input `.xlsx` file path.
* `-o`, `--output` <file>: Specify the output `.png` file path (defaults to the input name).
* `--t0` <date>: Reference date T0 (e.g. `2026-11-09` or `09/11/2026`). Calendar dates are replaced by offsets relative to T0 (blind planning): the axis is graduated in months (`T0 + 1 m`, same day of the following month) and no dates are written under the task names.
* `-h`, `--help`: Display help information showing all command-line options.
