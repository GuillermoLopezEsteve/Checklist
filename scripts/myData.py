import os
import json
import random
import tempfile


def get_sheet_url(demo_path_file: str):
    """Read a JSON file and return the value stored under 'file_url'
      (if present)."""
    with open(demo_path_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("file_url")


def get_tasks_file(g: int, data_path: str) -> str:
    """Build the path to a group's tasks file (e.g., data01.json)."""
    return os.path.join(
        data_path,
        f"data{g:02}.json",
    )


def get_demos_file(data_path: str) -> str:
    """Build the path to the demos excel export JSON."""
    return os.path.join(
        data_path, "excel.json")


def get_demo_data(group_number: int, data_path: str) -> dict:
    """
    Load demo completion data and split into:
    - done_demos: tasks with status == "TRUE"
    - pending_demos: everything else
    """
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


def get_tasks_data(g: int, data_path: str) -> dict:
    """Load tasks JSON for a specific group."""
    with open(get_tasks_file(g, data_path), 'r', encoding="utf-8") as file:
        data = json.load(file)
    return data


def get_all_groupdata_sorted(nGroups: int, data_path: str) -> list:
    """
    Compute group data for all groups and sort by:
    - points (desc)
    - random tie-breaker (desc) to shuffle same-score groups
    """
    data = []
    for i in range(1, nGroups+1):
        data.append(get_groupdata(i, data_path))
    for d in data:
        d["_rand"] = random.random()
    data.sort(key=lambda d: (d["points"], d["_rand"]), reverse=True)
    for d in data:
        d.pop("_rand", None)
    return data


def get_all_groupdata(nGroups: int, data_path: str) -> list:
    """
    Get all groups data in the same list
    """
    data = []
    for i in range(1, nGroups+1):
        data.append(get_groupdata(i, data_path))
    return data


def get_leaderboard_headers(data_path: str) -> list:
    """
    Build leaderboard headers:
    fixed columns + one "% <zone title>" column per zone.
    """
    r = ["Posició", "Grups", "Punts", "% Demo", "% Tasques"]
    for zone in get_tasks_data(1, data_path).get('zones'):
        r.append("% " + zone.get('title'))
    return r


def get_groupdata(number: int, data_path: str) -> dict:
    """
    Compute a group's leaderboard row data:
    - percent-demo: done demos / total demos
    - per-zone completion
    - percent-all-tasks: completed / total tasks
    - points: 1000 * (0.35*tasks% + 0.65*demos%)
    """
    gd = {}
    gd['name'] = f"Grup {number:02}"
    demoData = get_demo_data(number, data_path)
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
    for zone in get_tasks_data(number, data_path).get('zones'):
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


def transform_for_leaderboard(
    groupsData: list[dict],
    data_path: str
) -> tuple[list, list]:
    """
    Transform group dicts into a leaderboard table:
    - headers: list of column titles
    - rows: list of leaderboard rows
    """
    headers = get_leaderboard_headers(data_path)

    zones = get_tasks_data(1, data_path).get("zones", [])
    zone_titles = [z.get("title", "Zona") for z in zones]

    rows = []
    for idx, g in enumerate(groupsData, start=1):
        row = [
            idx,
            g.get("name", "NA"),
            g.get("points", 0),
            g.get("percent-demo", "0 %"),
            g.get("percent-all-tasks", "0 %"),
        ]

        for title in zone_titles:
            row.append(g.get(title, "0 %"))

        rows.append(row)

    return headers, rows


def store_task_data(g: int, data_path: str, data: dict) -> None:
    """Persist a group's tasks data back into its JSON file."""
    file_path = get_tasks_file(g, data_path)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


def randomize_task_data(n_groups: int, data_path: str) -> None:
    """Randomly assign 'OK' or 'Pending' to every task for each group."""
    for i in range(1, n_groups + 1):
        data = get_tasks_data(i, data_path)

        if not data:
            continue

        for zone in data.get("zones", []):
            for task in zone.get("tasks", []):
                task["status"] = random.choice(["OK", "Pending"])

        store_task_data(i, data_path, data)


def atomic_write_json(path: str, data: dict) -> None:
    """
    Atomically write JSON data to disk.

    Why this exists:
    - Prevents file corruption if the process crashes mid-write
    - Ensures readers always see a fully valid JSON file

    How it works:
    1. Write JSON to a temporary file in the same directory
    2. Flush and fsync to force data onto disk
    3. Atomically replace the target file using os.replace()

    os.replace() is atomic on POSIX filesystems when the
    source and destination are on the same filesystem.
    """
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=".tmp_", dir=os.path.dirname(path) or "."
        )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())  # ensure bytes hit disk
        os.replace(tmp_path, path)  # atomic on same filesystem
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


def update_demos_timestamp(path: str, time: str):
    timestamps = load_json(path)
    timestamps["demo"] = time
    atomic_write_json(path, timestamps)
    return


def load_json(path: str) -> dict:
    """
    Load a JSON file from disk safely.

    Behavior:
    - If the file does not exist → return empty dict
    - If the file is corrupted → rename it and return empty dict

    This prevents a single corrupted write from permanently
    breaking the application.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        # file corrupted; keep a backup and start fresh
        bak = path + ".corrupt"
        try:
            os.replace(path, bak)
        except Exception:
            pass
        return {}
