from flask import Flask, request, Response, render_template, send_from_directory
from datetime import datetime, timedelta
from flask import Blueprint, send_file, current_app, jsonify
from pathlib import Path
import scripts.myData as myData
import scripts.badges as badges
import json, sys, os


N_GROUPS = 12


app = Flask(__name__)
tasks_bp = Blueprint("tasks", __name__, url_prefix="/api")


@app.route("/requests", methods=["POST"])
def receive_request():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()

    group_id = data.get("Group_ID")
    tasks = data.get("data")

    if group_id is None:
        return jsonify({"error": "Group_ID is required"}), 400

    try:
        group_id = int(group_id)
    except (ValueError, TypeError):
        return jsonify({"error": "Group_ID must be a number"}), 400
    if tasks is None:
        return jsonify({"error": "task is required"}), 400

    data_path = f"data/dataf{group_id:02d}.json"

    try:
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2)
    except OSError as e:
        return jsonify({"error": "Failed to write task", "details": str(e)}), 500
    print("[SUCCESS] Recieved data from Group" + group_id)
    return jsonify({ "status": "success", "Group_ID": group_id }), 200




@tasks_bp.get("/tasks-data")
def tasksRequest():
    json_path = Path(current_app.root_path).parent / "config" / "tasks.json"
    return send_file(json_path, mimetype="application/json")


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
    integrantes = ["Juan Casas","Sonia Delgado"]
    return render_template('badges.html', number=number, medallas=medallas, integrantes=integrantes, demosDone=demosDone)


if __name__ == '__main__':
    N_GROUPS = 12
    app.run()

