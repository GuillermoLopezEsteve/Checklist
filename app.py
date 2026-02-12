from flask import (
    Flask, request, redirect, render_template,
    session, url_for, Blueprint, send_file,
    current_app, jsonify
)
from datetime import datetime, timedelta
from pathlib import Path
import scripts.myData as myData
import scripts.badges as badges
import scripts.src.myExcel as myExcel
import json
import os
import re
import shutil
from typing import Callable


N_GROUPS = 12

app = Flask(__name__)
app.secret_key = "supersecretkey"
tasks_bp = Blueprint("tasks", __name__, url_prefix="/api")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_TEMPLATE = "config/tasks.json"
DEMO_SRC = "config/demos.json"


@app.route("/api/update-tasks", methods=["GET", "POST"], strict_slashes=False)
def update_tasks():
    """
    Create or update the tasks JSON file for a specific group.

    - GET: returns a small help message.
    - POST: validates group_id, reads JSON payload, and stores it
      as dataXX.json inside the data directory.
    """
    if request.method == "GET":
        return jsonify({
            "ok": True,
            "hint": "Use POST with JSON body",
            "method": "GET"
        }), 200

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
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        return jsonify({
            "ok": True,
            "saved_as": str(out_path),
            "group_id": gid
        }), 200

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@tasks_bp.get("/tasks-data", strict_slashes=False)
def tasks_request():
    """
    Serve the base tasks template JSON file.

    This endpoint is used by the frontend to fetch the default
    task structure from config/tasks.json.
    """
    json_path = Path(current_app.root_path) / "config" / "tasks.json"

    if not json_path.exists():
        return jsonify({
            "error": "tasks.json not found",
            "searched_path": str(json_path)
        }), 404

    return send_file(json_path, mimetype="application/json")


@app.route("/")
def home():
    """
    Render the home page listing all available groups.
    """
    groups = [f"{i:02d}" for i in range(1, N_GROUPS + 1)]
    return render_template("home.html", groups=groups)


@app.route("/echo", methods=["POST"])
def echo():
    """
    Echo back the received JSON payload.

    Used mainly for testing connectivity and request handling.
    """
    return request.json, 200


@app.route("/group<number>")
def group_checklist(number: int):
    """
    Render the checklist page for a specific group.

    Loads:
    - task data for the group
    - demo completion data
    - next refresh timestamp
    """
    allTasks = myData.get_tasks_data(number, DATA_DIR)
    for zone in allTasks.get("zones", []):
        zone["id"] = zone.get("title", "").replace(" ", "")

    demo = myData.get_demo_data(number, DATA_DIR)
    time = datetime.now() + timedelta(minutes=5)

    return render_template(
        "checklist.html",
        number=number,
        allTasks=allTasks,
        demo=demo,
        next_update=time
    )


@app.route("/leaderboard")
def leaderboard():
    """
    Render the leaderboard page.

    Aggregates and sorts all group data, then transforms it
    into a table format for display.
    """
    leaderboardHeaders, leaderboardData = myData.transform_for_leaderboard(
        myData.get_all_groupdata_sorted(N_GROUPS, DATA_DIR),
        DATA_DIR
    )
    return render_template(
        "leaderboard.html",
        leaderboardHeaders=leaderboardHeaders,
        leaderboardData=leaderboardData
    )


@app.route("/group<number>/badges")
def medallas(number: int):
    """
    Render the badges page for a specific group.

    Displays earned badges and whether all demos are completed.
    """
    medallas = badges.get_badges_group(number, DATA_DIR)
    demosDone = badges.has_all_demos(number, DATA_DIR)
    return render_template(
        "badges.html",
        number=number,
        medallas=medallas,
        demosDone=demosDone
    )


app.register_blueprint(tasks_bp)


USERNAME = "admin"
PASSWORD = "admin123"


def check_auth(username: str, password: str) -> bool:
    """
    Validate provided credentials against the configured admin user.
    """
    return username == USERNAME and password == PASSWORD


def login_required(f: Callable):
    """
    Decorator that restricts access to authenticated users only.

    Redirects to the login page if the user is not logged in.
    """
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Handle user authentication.

    - GET: render login form
    - POST: validate credentials and start session
    """
    error: str | None = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if check_auth(username, password):
            session["logged_in"] = True
            return redirect(url_for("go_to_demo_sheet"))
        else:
            error = "Invalid credentials"

    return render_template("needs_auth.html", error=error)


@app.route("/logout")
def logout():
    """
    Log out the current user and clear the session.
    """
    session.pop("logged_in", None)
    return redirect(url_for("home"))


@login_required
@app.route("/admin")
def admin():
    """
    Render the admin dashboard.
    """
    return render_template("admin.html")


@app.route("/updates-demos", methods=["POST"])
def update_demos():
    """
    Fetch the latest demo data from Google Sheets
    and update the local demos JSON file.
    """
    myExcel.update_demo_data(DEMO_SRC)
    return redirect(url_for("admin"))


@app.route("/restart-tasks-data", methods=["POST"])
def restart_tasks_data():
    """
    Reset all group task files using the default task template.
    """
    for i in range(1, N_GROUPS + 1):
        filename = f"data{str(i).zfill(2)}.json"
        target_path = os.path.join(DATA_DIR, filename)
        shutil.copyfile(DATA_TEMPLATE, target_path)

    return redirect(url_for("admin"))


@app.route("/randomize-task-data", methods=["POST"])
def randomize_task_data():
    """
    Randomly assign task statuses for all groups.

    Intended for testing and demo purposes.
    """
    myData.randomize_task_data(N_GROUPS, DATA_DIR)
    return redirect(url_for("admin"))


@app.route("/demos-sheet")
@login_required
def go_to_demo_sheet():
    """
    Redirects to google sheets url, requieres auth
    """
    sheet_url = myData.get_sheet_url(DEMO_SRC)
    return redirect(sheet_url)


@app.errorhandler(404)
def not_found(error):
    """
    Render a custom 404 error page.
    """
    return render_template(
        "base_error.html",
        title="404 - Page Not Found",
        code="404",
        message="Page Not Found",
        description="The page you're looking for doesn't exist."
    ), 404


@app.errorhandler(500)
def internal_error(error):
    """
    Render a custom 500 error page.
    """
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
    """
    Render custom client-side error pages (400–403).
    """
    return render_template(
        "base_error.html",
        title=f"{error.code} - Error",
        code=error.code,
        message="Access Error",
        description=error.description
    ), error.code


def resolve_demo_data_endpoint(demos_config: str) -> None:
    """
    Ensure demos config contains a stable absolute 'data_endpoint'
    built from DATA_DIR + 'relative_data_endpoint'.

    Also creates the target directory if needed.
    """
    # Load config
    with open(demos_config, "r", encoding="utf-8") as f:
        data = json.load(f)
    rel = data.get("relative_data_endpoint")
    if not rel:
        print("Error no relative path")
        exit()
    full_path = os.path.abspath(os.path.join(DATA_DIR, rel))
    parent_dir = os.path.dirname(full_path)
    os.makedirs(parent_dir, exist_ok=True)
    data["data_endpoint"] = full_path
    with open(demos_config, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    """
    Application entry point.

    Ensures all group task files exist before starting
    the Flask development server.
    """
    N_GROUPS = 12
    for i in range(1, N_GROUPS + 1):
        filename = f"data{str(i).zfill(2)}.json"
        target_path = os.path.join(DATA_DIR, filename)

        if not os.path.exists(target_path):
            print(f"{target_path} not found. Creating from template...")
            shutil.copyfile(DATA_TEMPLATE, target_path)
        else:
            print(f"{target_path} already exists. Skipping.")

    resolve_demo_data_endpoint(DEMO_SRC)
    myExcel.update_demo_data(DEMO_SRC)

    app.run()
