import os
import json
import random


def get_sheet_url(demo_path_file: str):
    with open(demo_path_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("file_url")


def get_tasks_file(g: int, data_path: str) -> str:
    return os.path.join(
        data_path,
        f"data{g:02}.json",
    )


def get_demos_file(data_path: str) -> str:
    return os.path.join(
        data_path,
        "json", "excel.json")


def get_demo_data(group_number: int, data_path: str) -> dict:
    JSON_PATH = get_demos_file(data_path)
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    group_name = f"Grup {group_number:02}"
    if group_name not in data:
        raise KeyError(f"Group not found: {group_name}")

    done_demos = []
    pending_demos = []

    for task_name, status in data[group_name]:
        if status == "TRUE":
            done_demos.append(task_name)
        else:
            pending_demos.append(task_name)

    return {
        "group_name": group_name,
        "done_demos": done_demos,
        "pending_demos": pending_demos,
    }


def get_tasks_data(g: int, data_path: str):
    with open(get_tasks_file(g, data_path), 'r', encoding="utf-8") as file:
        data = json.load(file)
    return data


def getAllGroupDataSorted(nGroups):
    data = []
    for i in range(1, nGroups+1):
        data.append(getGroupData(i))
    data.sort(key=lambda d: d["points"], reverse=True)
    return data


def getAllGroupData(nGroups):
    data = []
    for i in range(1, nGroups+1):
        data.append(getGroupData(i))
    return data


def getLeaderboardTableHeaders(data_path: str):
    r = ["Posició", "Grups", "Punts", "% Demo", "% Tasques"]
    for zone in get_tasks_data(1, data_path).get('zones'):
        r.append("% " + zone.get('title'))
    return r


def getGroupData(number: int) -> dict:
    gd = {}
    gd['name'] = f"Grup {number:02}"
    demoData = get_demo_data(number)
    nPD = len(demoData['pending_demos'])
    nDD = len(demoData['done_demos'])
    vD = 0
    if nPD == 0 and nDD == 0:
        gd['percent-demo'] = "0%"
    else:
        vD = round((100 * nDD / (nPD + nDD)))
        gd['percent-demo'] = str(vD) + " %"
    vD = 0.65 * vD

    completedTasks = 0
    nTasks = 0
    for zone in get_tasks_data(number).get('zones'):
        title = zone.get('title')
        nZoneTasks = 0
        nZoneCompTask = 0
        for task in zone.get('tasks'):
            nTasks += 1
            nZoneTasks += 1
            if task.get('status') == "OK":
                completedTasks += 1
                nZoneCompTask += 1
        gd[title] = str(round(100 * (nZoneCompTask / nZoneTasks))) + " %"

    vT = 0
    if nTasks != 0:
        vT = round(100 * completedTasks / nTasks)
    gd['percent-all-tasks'] = str(vT) + " %"
    vT = 0.35 * vT
    gd['points'] = round(1000 * (vT + vD))
    return gd


def tranformForLeaderboard(groupsData):
    i = 1
    data = []
    for g in groupsData:
        gD = [i]
        i += 1
        gD.append(g.pop("name", "NA"))
        gD.append(g.pop("points", "0"))
        gD.append(g.pop("percent-demo", "0%"))
        gD.append(g.pop("percent-all-tasks", "0%"))
        for zone in get_tasks_data(1).get('zones'):
            gD.append(g.get(zone.get('title')))
        data.append(gD)
    return data


def store_task_data(g: int, data_path: str, data: dict) -> None:
    file_path = get_tasks_file(g, data_path)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


def randomize_task_data(n_groups: int, data_path: str) -> None:
    for i in range(1, n_groups + 1):
        data = get_tasks_data(i, data_path)

        if not data:
            continue

        for zone in data.get("zones", []):
            for task in zone.get("tasks", []):
                task["status"] = random.choice(["OK", "Pending"])

        store_task_data(i, data_path, data)
