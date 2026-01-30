from . import myData
import os

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

def convertBadgeToImg(str):
    return os.path.join(
        os.path.dirname(__file__),
        "..",
        "static",
        str.replace(" ","")+".png",
    )


