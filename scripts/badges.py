from . import myData
import os, json

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

def allGroupBadges(nGroups):
    dG = myData.getAllGroupData(nGroups)
    badges = []
    for g in dG:
        gBadges = {}
        gBadges["name"] = g.get("name");
        medallas = []
        for zone in myData.get_tasks_data(1).get('zones'):
           if "100 %" == g.get(zone.get('title')):
                medallas.append(convertBadgeToImg(zone.get('title')))
        gBadges["medallas"] = medallas
        badges.append(gBadges)
    return badges

def convertBadgeToImgSrc(key_dict):
    return "/static/" + dict_id_images.get(key_dict)



def getBadgesGroup(number):
    with open(myData.get_tasks_file(number), "r", encoding="utf-8") as f:
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

def hasAllDemos(number):
    demoData = myData.get_demo_data(number)
    return len(demoData["pending_demos"]) == 0


def hasBadges(number):
    return len(getBadgesGroup(number)) > 0




