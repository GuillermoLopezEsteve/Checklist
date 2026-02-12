import pandas as pd
import json
import os
from datetime import datetime


def log_success(message: str) -> None:
    """Print a success message with a timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def read_data(df: pd.DataFrame) -> dict:
    """
    Read a dataframe exported from Google Sheets and return:
    {
        group_id: [[task_name, value], ...],
        ...
    }
    """
    alltasks: dict = {}

    for row_idx in range(len(df)):
        # Skip header row
        if row_idx == 0:
            continue

        g = df.iat[row_idx, 0]
        tasks: list[list] = []

        for col_idx in range(1, len(df.columns)):
            cell_value = df.iat[row_idx, col_idx]
            t = [df.iat[0, col_idx], cell_value]
            tasks.append(t)

        alltasks[g] = tasks

    return alltasks


def load_demos_from_sheets(sheet_url: str, data_path: str) -> None:
    """
    Download demo data from a Google Sheet (CSV export) and store it as JSON.

    Any error during download, parsing, or file writing is caught and printed
    instead of crashing the application.
    """
    try:
        csv_url = sheet_url.replace("/edit#gid=", "/export?format=csv&gid=")
        demos = read_data(pd.read_csv(csv_url))

        # Ensure output directory exists
        out_dir = os.path.dirname(os.path.abspath(data_path))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        # Write JSON file
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(demos, f, ensure_ascii=False, indent=2)
        log_success("Updated Demos Data")

    except Exception as exc:
        # Timestamped, explicit error output
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] ERROR updating demos data:")
        print(str(exc))

        # Optional: full traceback for debugging
        import traceback
        traceback.print_exc()


def get_demo_data(demos_path: str) -> tuple[str | None, str | None]:
    """
    Read demo configuration JSON and return:
    (sheet_url, data_endpoint)
    """
    with open(demos_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("file_url"), data.get("data_endpoint")


def update_demo_data(data_file_path: str) -> None:
    """
    High-level helper that:
    1. Reads demo config
    2. Downloads demo data
    3. Updates local JSON
    """
    sheet_url, demos_data_path = get_demo_data(data_file_path)
    load_demos_from_sheets(sheet_url, demos_data_path)
