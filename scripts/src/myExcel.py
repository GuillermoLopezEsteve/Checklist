import pandas as pd
import json, os

from datetime import datetime

def log_success(message: str):
    """Print a success message with a timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

# Example usage
def update_demos():
    # ... your code to update demos ...
    log_success("Successfully updated demos data")

def update_tasks():
    # ... your code to update tasks ...
    log_success("Successfully updated tasks data")

if __name__ == "__main__":
    update_demos()
    update_tasks()


def readData(df):
    alltasks = {}
    for row_idx in range(len(df)):
        if row_idx == 0:
            continue

        g = df.iat[row_idx, 0]
        tasks = []
        for col_idx in range(1, len(df.columns)):
            cell_value = df.iat[row_idx, col_idx]
            t = [df.iat[0, col_idx], cell_value]
            tasks.append(t)

        alltasks[g] = tasks

    return alltasks


def loadDemosFromExcel(sheet_url, data_path):
    csv_url = sheet_url.replace("/edit#gid=", "/export?format=csv&gid=")
    demos = readData(pd.read_csv(csv_url))

    # Ensure output directory exists
    out_dir = os.path.dirname(os.path.abspath(data_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    # Write JSON file
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(demos, f, ensure_ascii=False, indent=2)

    log_success("Updated Demos Data")

