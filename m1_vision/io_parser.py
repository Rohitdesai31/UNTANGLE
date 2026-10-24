import json
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {
    "Tag",
    "Description",
    "Type",
    "Process Variable",
    "Loop / Number",
}


def parse_io_excel(input_path: str, output_path: str):
    """Parse an IO Excel file and save a normalized io_list.json."""

    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(
            f"IO Excel file not found: {input_path}"
        )

    df = pd.read_excel(input_path)

    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    io_list = []

    for _, row in df.iterrows():
        item = {
            "tag": str(row["Tag"]).strip(),
            "type": str(row["Type"]).strip(),
            "description": str(row["Description"]).strip(),
            "loop": (
                f"{str(row['Process Variable']).strip()} "
                f"{str(row['Loop / Number']).strip()}"
            ),
        }

        # Preserve status when the column exists.
        if "Expected Status" in df.columns:
            item["expected_status"] = str(
                row["Expected Status"]
            ).strip()

        io_list.append(item)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    data = io_list

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            indent=2
        )

    print(f"IO entries parsed: {len(io_list)}")
    print(f"IO list saved: {output_path}")

    return data