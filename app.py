from flask import Flask, request, Response, render_template, jsonify, send_from_directory
from datetime import datetime, timedelta
import scripts.myData as myData
import scripts.badges as badges
import json
import os


N_GROUPS = 12


app = Flask(__name__)


@app.route('/')
def home():
    groups = [f"{i:02d}" for i in range(1, N_GROUPS + 1) ]
    return render_template('home.html', groups=groups)

@app.route('/group<number>')
def group_checklist(number):
    allTasks = myData.get_tasks_data(number)
    for zone in allTasks.get("zones"):
        zone["id"] = zone.get("title").replace(" ", "")
    demo = myData.get_demo_data(number)
    time = datetime.now() + timedelta(minutes=5)
    tieneMedallas = badges.hasBadges(number)
    return render_template('checklist.html', tieneMedallas=tieneMedallas, number=number, allTasks=allTasks, demo=demo, next_update=time)


@app.route('/leaderboard')
def leaderboard():
    leaderboardHeaders = myData.getLeaderboardTableHeaders()
    leaderboardData = myData.tranformForLeaderboard(myData.getAllGroupDataSorted(N_GROUPS))
    return render_template('leaderboard.html', leaderboardHeaders=leaderboardHeaders, leaderboardData=leaderboardData)

@app.route('/group<number>/badges')
def medallas(number):
    medallas = badges.getBadgesGroup(number)
    demosDone = badges.hasAllDemos(number)
    return render_template('badges.html', number=number, medallas=medallas, demosDone=demosDone)


if __name__ == '__main__':

    app.run(
        host='0.0.0.0',
        port=8443,
        ssl_context=('CA/certs/web.crt', 'CA/certs/web.pem'),
        debug=False
    )
