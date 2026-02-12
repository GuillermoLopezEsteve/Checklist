from . import myData
import json

dict_id_images = {
    "REMOTE-ACCESS": "badges/badge_remoteacces.png",
    "DNS": "badges/badge_dns.png",
    "WEB": "badges/badge_web.png",
    "MAIL": "badges/badge_mail.png",
    "WORDPRESS": "badges/badge_wordpress.png",
    "BACKUP": "badges/badge_backups.png",
    "Scripting": "badges/badge_scripting.png",
    "FTP": "badges/badge_ftp.png"
}


def convertBadgeToImgSrc(key_dict):
    return "/static/" + dict_id_images.get(key_dict)


def getBadgesGroup(number, data_path: str):
    with open(
        myData.get_tasks_file(number, data_path), "r", encoding="utf-8"
    ) as f:
        groupTasks = json.load(f)
    badgeGroup = []
    for zone in groupTasks.get("zones"):
        allTasksDone = True
        for task in zone.get("tasks"):
            if task.get("status") != "OK":
                allTasksDone = False
        b = {"id": zone.get("id"), "title": zone.get("title")}
        b["source"] = convertBadgeToImgSrc(zone.get("id"))
        b["shadow"] = True
        if allTasksDone:
            b["shadow"] = False
        badgeGroup.append(b)
    return badgeGroup


def hasAllDemos(number, data_path: str):
    demoData = myData.get_demo_data(number, data_path)
    return len(demoData["pending_demos"]) == 0


def hasBadges(number):
    return len(getBadgesGroup(number)) > 0
