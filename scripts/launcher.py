#!/etc/checklist/venv/bin/python

import src.myExcel as myExcel
import sys
import json

def getDemoData(demos_path: str):
    with open(demos_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("file_url"), data.get("data_endpoint")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(
            "Usage: python3 launcher.py <demos.json>")
        sys.exit(1)

    config = {
        "demos": sys.argv[1],
    }

    sheet_url, demos_data_path = getDemoData(config["demos"])
    myExcel.loadDemosFromExcel(sheet_url, demos_data_path)
