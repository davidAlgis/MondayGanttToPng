import argparse
import csv
import os
import re
import xml.etree.ElementTree as ET
import zipfile


def get_col_index(cell_ref):
    """Convert cell reference (e.g., 'A1', 'B3', 'AA5') to a 0-based column index."""
    match = re.match(r"([A-Z]+)([0-9]+)", cell_ref)
    if match:
        col_str = match.group(1)
        idx = 0
        for char in col_str:
            idx = idx * 26 + (ord(char) - ord("A") + 1)
        return idx - 1
    return None


def convert_xlsx_to_csv_manual(input_path, output_path):
    if not output_path:
        output_path = os.path.splitext(input_path)[0] + ".csv"

    try:
        with zipfile.ZipFile(input_path, "r") as z:

            # --- 1. SHARED STRINGS ---
            strings = []
            if "xl/sharedStrings.xml" in z.namelist():
                sst_xml = ET.fromstring(z.read("xl/sharedStrings.xml"))
                ns = {
                    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
                }
                for si in sst_xml.findall("main:si", ns):
                    t = si.find("main:t", ns)
                    strings.append(t.text if t is not None else "")

            # --- 2. SHEET DATA ---
            sheet_xml = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
            ns = {
                "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
            }

            rows = []
            for row in sheet_xml.findall(".//main:row", ns):
                current_row = {}
                max_idx = -1
                for c in row.findall("main:c", ns):
                    ref = c.get("r")
                    if not ref:
                        continue
                    idx = get_col_index(ref)
                    if idx is None:
                        continue
                    if idx > max_idx:
                        max_idx = idx

                    v = c.find("main:v", ns)
                    val = ""
                    if v is not None:
                        val = v.text
                        if c.get("t") == "s":
                            val = strings[int(val)]
                    current_row[idx] = val

                # Safely construct the full row list padding empty cells
                if max_idx >= 0:
                    row_list = [""] * (max_idx + 1)
                    for idx, val in current_row.items():
                        row_list[idx] = val
                    rows.append(row_list)
                else:
                    rows.append([])

            # --- 3. CSV WRITING ---
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            print(
                f"Successfully bypassed XML validation and created '{output_path}'"
            )

    except Exception as e:
        print(f"Manual extraction failed: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Emergency XLSX to CSV converter (ignores style errors)"
    )
    parser.add_argument(
        "-i", "--input", required=True, help="Input .xlsx file path"
    )
    parser.add_argument(
        "-o", "--output", help="Output .csv file path (default: same as input)"
    )
    args = parser.parse_args()

    convert_xlsx_to_csv_manual(args.input, args.output)