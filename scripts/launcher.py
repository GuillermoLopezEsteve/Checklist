#!/etc/checklist/venv/bin/python
import src.myExcel as myExcel
import sys

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(
            "Usage: python3 launcher.py <demos.json>")
        sys.exit(1)

    config = {
        "demos": sys.argv[1],
    }

    myExcel.update_demo_data(config["demos"])
