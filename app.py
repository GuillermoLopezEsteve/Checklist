from flask import Flask, request, Response, render_template, jsonify, send_from_directory
from datetime import datetime, timedelta
import scripts.data as data
import scripts.badges as badges
import json
import os


N_GROUPS = 12


app = Flask(__name__)


@app.route('/')
def home():
    groups = [f"{i:02d}" for i in range(1, N_GROUPS + 1) ]
    medallas = badges.allGroupBadges(N_GROUPS)
    return render_template('home.html', groups=groups, medallas=medallas)

@app.route('/group<number>')
def group_checklist(number):
    allTasks = data.get_tasks_data(number)
    demo = data.get_demo_data(number)
    time = datetime.now() + timedelta(minutes=5)
    return render_template('checklist.html', number=number, allTasks=allTasks, demo=demo, next_update=time)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'media'),
                               'favicon.ico', mimetype='webp')
@app.route('/leaderboard')
def leaderboard():
    leaderboardHeaders = data.getLeaderboardTableHeaders()
    leaderboardData = data.tranformForLeaderboard(data.getAllGroupDataSorted(N_GROUPS))
    return render_template('leaderboard.html', leaderboardHeaders=leaderboardHeaders, leaderboardData=leaderboardData)


if __name__ == '__main__':
    #app.add_url_rule("/favicon.ico",endpoint="favicon",redirect_to=url_for("static", filename="favicon.ico"),)

    app.run(
        host='0.0.0.0',
        port=8443,
        ssl_context=('CA/certs/web.crt', 'CA/certs/web.pem'),
        debug=False
    )
