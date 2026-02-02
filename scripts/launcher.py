import sys, json, os
import myExcel from lib.myExcel
import myTasks from lib.myTasks


config = {"servers": None, "tasks": None, "demos": None, "dataFolder": None}



if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python3 launcher.py <servers.json> <tasks.json> <demos.json> <dataFolder>")
        sys.exit(1)

    config = {
        "servers": sys.argv[1],
        "tasks": sys.argv[2],
        "demos": sys.argv[3],
        "dataFolder": sys.argv[4]
    }

    myExcel.loadDemosFromExcel(config.get("demos"), config.get("dataFolder"))
    myTasks.loadTasksFromRemote(config.get("tasks"), config.get("servers"), config.get("dataFolder"))
