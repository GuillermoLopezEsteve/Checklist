from . import myData
import json

# Map zone/badge IDs to their image paths (relative to /static/)
dict_id_images = {
    "REMOTE-ACCESS": "badges/badge_remoteacces.png",
    "DNS": "badges/badge_dns.png",
    "WEB": "badges/badge_web.png",
    "MAIL": "badges/badge_mail.png",
    "WORDPRESS": "badges/badge_wordpress.png",
    "BACKUP": "badges/badge_backups.png",
    "SCRIPTING": "badges/badge_scripting.png",
    "FTP": "badges/badge_ftp.png",
}


def convert_badges_imgsrc(key_dict: str) -> str:
    """
    Convert a badge/zone ID into a static image URL.
    Falls back to an empty string if the key is not found.
    """
    rel_path = dict_id_images.get(key_dict)
    if rel_path is None:
        return ""
    return "/static/" + rel_path


def get_badges_group(g: int, data_path: str) -> list[dict]:
    """
    Build the list of badge descriptors for a group.
    A badge gets 'shadow'=False if all tasks in its zone are completed ("OK").
    """
    with open(myData.get_tasks_file(g, data_path), "r", encoding="utf-8") as f:
        groupTasks = json.load(f)

    badgeGroup: list[dict] = []

    for zone in groupTasks.get("zones", []):
        # Determine whether every task in the zone is complete
        allTasksDone = True
        for task in zone.get("tasks", []):
            if task.get("status") != "OK":
                allTasksDone = False
                break

        zone_id = zone.get("id", "")
        b = {
            "id": zone_id,
            "title": zone.get("title", ""),
            "source": convert_badges_imgsrc(zone_id),
            "shadow": not allTasksDone,
        }
        badgeGroup.append(b)

    return badgeGroup


def has_all_demos(g: int, data_path: str) -> bool:
    """Return True if the group has no pending demos."""
    demoData = myData.get_demo_data(g, data_path)
    return len(demoData.get("pending_demos", [])) == 0


def hasBadges(g: int, data_path: str) -> bool:
    """
    Return True if the group has at least one badge entry.
    """
    return len(get_badges_group(g, data_path)) > 0
