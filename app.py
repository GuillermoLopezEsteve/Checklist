from flask import Flask, request, redirect, render_template, session, url_for
from datetime import datetime, timedelta
from flask import Blueprint, send_file, current_app, jsonify
from pathlib import Path
import scripts.myData as myData
import scripts.badges as badges
import json
import os
import re
import shutil


N_GROUPS = 12  # Default, passed via main

app = Flask(__name__)
app.secret_key = "supersecretkey"  # change in production
tasks_bp = Blueprint("tasks", __name__, url_prefix="/api")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_TEMPLATE = "config/tasks.json"
DEMO_SRC = "config/demos.json"


@app.route("/api/update-tasks", methods=["GET", "POST"], strict_slashes=False)
def updateTasks():
    if request.method == "GET":
        return jsonify({
            "ok": True,
            "hint": "Use POST with JSON body",
            "method": "GET"}
        ), 200

    try:
        group_id = request.args.get("group_id", "")
        if not group_id:
            return jsonify({"error": "Missing group_id query param"}), 400
        if not re.fullmatch(r"\d+", group_id):
            return jsonify({"error": "group_id must be numeric"}), 400

        gid = str(int(group_id)).zfill(2)
        payload = request.get_json(force=True, silent=True)
        if payload is None:
            return jsonify({"error": "Request body must be JSON"}), 400

        out_path = DATA_DIR / f"data{gid}.json"
        out_path.write_text(
            json.dumps(
                payload, ensure_ascii=False, indent=2), encoding="utf-8")

        return jsonify(
            {"ok": True, "saved_as": str(out_path), "group_id": gid}), 200

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@tasks_bp.get("/tasks-data", strict_slashes=False)
def tasksRequest():
    json_path = Path(current_app.root_path) / "config" / "tasks.json"

    if not json_path.exists():
        return jsonify({
            "error": "tasks.json not found",
            "searched_path": str(json_path)
        }), 404

    return send_file(json_path, mimetype="application/json")


@app.route('/')
def home():
    groups = [f"{i:02d}" for i in range(1, N_GROUPS + 1)]
    return render_template('home.html', groups=groups)


@app.route("/echo", methods=["POST"])
def echo():
    # simple test endpoint
    from flask import request
    return request.json, 200


@app.route('/group<number>')
def group_checklist(number):
    allTasks = myData.get_tasks_data(number, DATA_DIR)
    for zone in allTasks.get("zones"):
        zone["id"] = zone.get("title").replace(" ", "")
    demo = myData.get_demo_data(number, DATA_DIR)
    time = datetime.now() + timedelta(minutes=5)
    return render_template(
        'checklist.html',
        number=number, allTasks=allTasks, demo=demo, next_update=time)


@app.route('/leaderboard')
def leaderboard():
    leaderboardHeaders = myData.getLeaderboardTableHeaders(DATA_DIR)
    leaderboardData = myData.tranformForLeaderboard(
        myData.getAllGroupDataSorted(N_GROUPS))
    return render_template(
        'leaderboard.html',
        leaderboardHeaders=leaderboardHeaders, leaderboardData=leaderboardData)


@app.route('/group<number>/badges')
def medallas(number):
    medallas = badges.getBadgesGroup(number, DATA_DIR)
    demosDone = badges.hasAllDemos(number, DATA_DIR)
    return render_template(
        'badges.html', number=number, medallas=medallas, demosDone=demosDone)


app.register_blueprint(tasks_bp)


USERNAME = "admin"
PASSWORD = "admin123"


def check_auth(username, password):
    return username == USERNAME and password == PASSWORD


def login_required(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if check_auth(username, password):
            session["logged_in"] = True
            return redirect(url_for("goToDemos"))
        else:
            error = "Invalid credentials"
    return render_template("needs_auth.html", error=error)


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("home"))


@login_required
@app.route("/admin")
def admin():
    return render_template("admin.html")


@app.route("/updates-demos", methods=["POST"])
def update_demos():
    myData.updateDemos(DEMO_SRC)
    return redirect(url_for("admin"))


@app.route("/restart-tasks-data", methods=["POST"])
def restart_tasks_data():
    for i in range(1, N_GROUPS + 1):
        filename = f"data{str(i).zfill(2)}.json"
        target_path = os.path.join(DATA_DIR, filename)
        shutil.copyfile(DATA_TEMPLATE, target_path)
    return redirect(url_for("admin"))


@app.route("/randomize-task-data", methods=["POST"])
def randomize_task_data():
    myData.randomize_task_data(N_GROUPS, DATA_DIR)
    return redirect(url_for("admin"))


@app.route("/demos-sheet")
@login_required
def goToDemos():
    return redirect(myData.get_sheet_url(DEMO_SRC))
# "https://docs.google.com/spreadsheets/d/1cma0J7eTugMeRtG8VCHbYiHb5RlJ6TLK_SPYUoxfDFA")


@app.errorhandler(404)
def not_found(error):
    return render_template(
        "base_error.html",
        title="404 - Page Not Found",
        code="404",
        message="Page Not Found",
        description="The page you're looking for doesn't exist."
    ), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template(
        "base_error.html",
        title="500 - Server Error",
        code="500",
        message="Something went wrong",
        description="We're experiencing technical difficulties."
    ), 500


@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(403)
def client_error(error):
    return render_template(
        "base_error.html",
        title=f"{error.code} - Error",
        code=error.code,
        message="Access Error",
        description=error.description
    ), error.code


if __name__ == '__main__':
    N_GROUPS = 12
    for i in range(1, N_GROUPS + 1):
        filename = f"data{str(i).zfill(2)}.json"
        target_path = os.path.join(DATA_DIR, filename)

        if not os.path.exists(target_path):
            print(f"{target_path} not found. Creating from template...")
            shutil.copyfile(DATA_TEMPLATE, target_path)
        else:
            print(f"{target_path} already exists. Skipping.")
    app.run()
