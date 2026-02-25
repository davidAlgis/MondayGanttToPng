import argparse
import os
import sys

# Import the core functions from your previous scripts
try:
    from csv_to_png import generate_png
    from xlsx_to_csv import convert_xlsx_to_csv_manual
except ImportError:
    print(
        "Error: Ensure 'xlsx_to_csv.py' and 'csv_to_png.py' are in this directory."
    )
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Convert XLSX directly to a modern Gantt PNG."
    )
    parser.add_argument(
        "-i", "--input", required=True, help="Path to the source .xlsx file"
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Path for the final .png file (default: same as input)",
    )

    args = parser.parse_args()

    # 1. Define paths
    input_xlsx = args.input
    base_name = os.path.splitext(input_xlsx)[0]
    temp_csv = f"{base_name}_temp_data.csv"
    output_png = args.output if args.output else f"{base_name}.png"

    try:
        # Step 1: XLSX -> CSV (Surgical extraction bypassing style errors)
        print(f"--- Step 1: Extracting data from {input_xlsx} ---")
        convert_xlsx_to_csv_manual(input_xlsx, temp_csv)

        # Step 2: CSV -> PNG (Modern Monday-style rendering)
        if os.path.exists(temp_csv):
            print(
                f"--- Step 2: Generating modern Gantt chart: {output_png} ---"
            )
            generate_png(temp_csv, output_png)
        else:
            print(
                "Error: Temporary CSV was not created. Check Step 1 for errors."
            )

    except Exception as e:
        print(f"Pipeline failed: {e}")

    finally:
        # Step 3: Cleanup
        if os.path.exists(temp_csv):
            os.remove(temp_csv)
            print(f"--- Cleanup: Removed temporary file {temp_csv} ---")


if __name__ == "__main__":
    main()
