import random, os, json, math


def get_tasks_file(g: int) -> str:
    return os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        f"data{g:02}.json",
    )

def get_demos_file() -> str:
    return os.path.join(
        os.path.dirname(__file__),
        "..","data","json","excel.json"
    )

def get_demo_data(group_number: int) -> dict:
    JSON_PATH = get_demos_file()
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


def get_tasks_data(g: int):
    with open(get_tasks_file(g), 'r') as file:
        data = json.load(file)
    return data

def getAllGroupDataSorted(nGroups):
    data=[]
    for i in range(1,nGroups+1):
      data.append(getGroupData(i))
    data.sort(key=lambda d: d["points"], reverse=True)
    return data

def getAllGroupData(nGroups):
    data=[]
    for i in range(1,nGroups+1):
      data.append(getGroupData(i))
    return data

def getLeaderboardTableHeaders():
    r = ["Posició", "Grups", "Punts", "% Demo", "% Tasques"]
    for zone in get_tasks_data(1).get('zones'):
        r.append("% " + zone.get('title'))
    return r

def getGroupData(number: int)-> dict:
    gd = {}
    gd['name']   = f"Grup {number:02}"
    demoData  = get_demo_data(number)
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


    gd['points'] = round(1000* (vT + vD))
    return gd

def tranformForLeaderboard(groupsData):
    #Order: ["Posició", "Grups", "Punts", "% Demo", "% Tasques", ..[Tasques]..]
    i = 1
    data = []
    for g in groupsData:
        gD = [i]; i += 1
        gD.append(g.pop("name", "NA"))
        gD.append(g.pop("points", "0"))
        gD.append(g.pop("percent-demo", "0%"))
        gD.append(g.pop("percent-all-tasks", "0%"))
        for zone in get_tasks_data(1).get('zones'):
           gD.append(g.get(zone.get('title')))
        data.append(gD)
    return data;

