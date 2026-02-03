#!/etc/checklist/venv/bin/python

import sys, json, os
import src.myExcel as myExcel
import src.myTasks as myTasks


def getDemoData(demos_path: str):
    with open(demos_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("file_url"), data.get("data_endpoint")


if __name__ == "__main__":
    # Optional: make relative paths consistent under cron
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    os.chdir(BASE_DIR)

    if len(sys.argv) != 4:
        print("Usage: python3 launcher.py <servers.json> <tasks.json> <demos.json>")
        sys.exit(1)

    config = {
        "servers": sys.argv[1],
        "tasks": sys.argv[2],
        "demos": sys.argv[3],
    }

    sheet_url, demos_data_path = getDemoData(config["demos"])
    myExcel.loadDemosFromExcel(sheet_url, demos_data_path)
