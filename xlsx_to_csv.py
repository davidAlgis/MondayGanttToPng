import argparse
import csv
import os
import xml.etree.ElementTree as ET
import zipfile


def convert_xlsx_to_csv_manual(input_path, output_path):
    """
    WHY THIS APPROACH?
    Standard libraries (Pandas/OpenPyXL) try to validate the entire Excel structure,
    including styles, formatting, and metadata. If the 'styles.xml' file is
    malformed, they crash.

    This method bypasses validation by:
    1. Treating the XLSX as a ZIP file.
    2. Extracting raw text from 'sharedStrings.xml'.
    3. Extracting raw cell values from 'sheet1.xml'.
    4. Ignoring all styling/formatting data entirely.
    """

    if not output_path:
        output_path = os.path.splitext(input_path)[0] + ".csv"

    try:
        # XLSX files are actually ZIP archives containing XML files
        with zipfile.ZipFile(input_path, "r") as z:

            # --- 1. SHARED STRINGS ---
            # To save space, Excel doesn't store the same text multiple times.
            # It stores a unique list of strings in one file, and cells just
            # reference an index (e.g., "Cell A1 uses String #5").
            strings = []
            if "xl/sharedStrings.xml" in z.namelist():
                sst_xml = ET.fromstring(z.read("xl/sharedStrings.xml"))
                # Excel XML uses specific namespaces that must be declared for searching
                ns = {
                    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
                }
                for si in sst_xml.findall("main:si", ns):
                    t = si.find("main:t", ns)
                    strings.append(t.text if t is not None else "")

            # --- 2. SHEET DATA ---
            # We open the first worksheet directly.
            # This bypasses 'xl/styles.xml' where your specific error occurs.
            sheet_xml = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
            ns = {
                "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
            }

            rows = []
            # Iterate through every row tag in the XML
            for row in sheet_xml.findall(".//main:row", ns):
                current_row = []
                # Iterate through every cell ('c') in the row
                for c in row.findall("main:c", ns):
                    v = c.find("main:v", ns)  # 'v' is the value tag
                    if v is not None:
                        val = v.text
                        # If the cell attribute 't' is 's', it means 'Shared String'.
                        # We use the value as an index to get the actual text.
                        if c.get("t") == "s":
                            val = strings[int(val)]
                        current_row.append(val)
                    else:
                        # Handle empty cells
                        current_row.append("")
                rows.append(current_row)

            # --- 3. CSV WRITING ---
            # Standard python 'csv' module is used to ensure proper quoting/escaping
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            print(
                f"Successfully bypassed XML validation and created '{output_path}'"
            )

    except Exception as e:
        # This will catch issues like missing sheet1.xml or corrupted ZIP structures
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
