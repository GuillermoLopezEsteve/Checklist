from flask import (
    Flask, request, redirect, render_template,
    session, url_for, Blueprint, send_file,
    current_app, jsonify, abort
)
from werkzeug.middleware.proxy_fix import ProxyFix
from authlib.integrations.flask_client import OAuth
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import scripts.myData as myData
import scripts.badges as badges
import scripts.src.myExcel as myExcel
import json
import os
import re
import shutil
import sys
from typing import Callable

app = Flask(__name__)

N_GROUPS = 12

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
TIMESTAMP_PATH = "data/timestamps.json"
DATA_TEMPLATE = BASE_DIR / "config/tasks.json"
DEMO_SRC = BASE_DIR / "config/demos.json"

tasks_bp = Blueprint("tasks", __name__, url_prefix="/api")
KEY_PATH = BASE_DIR / ".secret" / "ACCESS_KEY_PROD"
try:
    app.secret_key = KEY_PATH.read_text().strip()
except FileNotFoundError:
    print(f"Warning: Secret key file not found at {KEY_PATH}")
    app.secret_key = "dev-key-only-use-in-local"

GOOGLE_CLIENT_ID_PATH = BASE_DIR / ".secret" / "GOOGLE_CLIENT_ID"
GOOGLE_CLIENT_ID_SECRET_PATH = BASE_DIR / ".secret" / "GOOGLE_CLIENT_SECRET"
app.config['GOOGLE_CLIENT_ID'] = GOOGLE_CLIENT_ID_PATH.read_text().strip()
app.config['GOOGLE_CLIENT_SECRET'] = GOOGLE_CLIENT_ID_SECRET_PATH.read_text().strip()
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
oauth = OAuth(app)
google = oauth.register(
  name='google',
  server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
  client_kwargs={'scope': 'openid email profile'}
)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '0'
app.config['PREFERRED_URL_SCHEME'] = 'https'


@app.route("/api/update-tasks", methods=["GET", "POST"], strict_slashes=False)
def update_tasks():
    """
    Create or update the tasks JSON file for a specific group.

    - GET: returns a small help message.
    - POST: validates group_id, reads JSON payload, and stores it
      as dataXX.json inside the data directory. Updates timestamp file also
      in data directory.
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

        payload = request.get_json(force=True, silent=True)
        tasks_data = payload.get("tasks")
        if tasks_data is None:
            return jsonify({"error": "Request body must be JSON, missing tasks_data"}), 400
        counts = payload.get("counts") or {}
        if counts is None:
            return jsonify({"error": "Request body must be JSON, missing counts"}), 400

        store_timestamp(TIMESTAMP_PATH, group_id, counts)

        gid = str(int(group_id)).zfill(2)

        out_path = DATA_DIR / f"data{gid}.json"
        out_path.write_text(
            json.dumps(tasks_data, ensure_ascii=False, indent=2),
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


@app.route("/group<number>", strict_slashes=False)
def group_checklist(number: int):
    """
    Render the checklist page for a specific group.

    Loads:
    - task data for the group
    - demo completion data
    - next refresh timestamp
    """
    try:
        allTasks = myData.get_tasks_data(number, DATA_DIR)
    except FileNotFoundError:
        gid = str(int(number)).zfill(2)
        dest = DATA_DIR / f"data{gid}.json"
        shutil.copyfile(DATA_TEMPLATE, dest)
        allTasks = myData.get_tasks_data(number, DATA_DIR)
    for zone in allTasks.get("zones", []):
        zone["id"] = zone.get("title", "").replace(" ", "")

    demo = myData.get_demo_data(number, DATA_DIR)
    time = datetime.now() + timedelta(minutes=5)
    # print(demo)
    return render_template(
        "checklist.html",
        number=number,
        allTasks=allTasks,
        demo=demo,
        next_update=time
    )


@app.route("/leaderboard", strict_slashes=False)
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


@app.route("/group<number>/badges", strict_slashes=False)
def medallas(number: int):
    """
    Render the badges page for a specific group.
    Displays earned badges and whether all demos are completed.
    """
    medallas = badges.get_badges_group(number, DATA_DIR)
    demosDone = badges.has_all_demos(number, DATA_DIR)
    # print(medallas)
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
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


ALLOWED_EMAILS_PATH = BASE_DIR / ".secret" / "ALLOWED_EMAILS"
ALLOWED_EMAILS = [
    line.strip()
    for line in ALLOWED_EMAILS_PATH.read_text().splitlines()
    if line.strip()
]


@app.route('/auth/callback')
@app.route('/auth/callback')
def auth_callback():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    email = user_info.get('email')

    if email in ALLOWED_EMAILS:
        session['user'] = user_info
        target = session.pop('next_url', url_for('home'))
        return redirect(target)
    else:
        abort(403, description="USER IS NOT ALLOWED AS ADMIN")


@app.route('/login')
def login():
    next_url = request.args.get('next')
    if next_url:
        session['next_url'] = next_url
    redirect_uri = url_for('auth_callback', _external=True)
    print(f"DEBUG REDIRECT URI: {redirect_uri}")
    return google.authorize_redirect(redirect_uri)


"""
@app.route("/login", methods=["GET", "POST"], strict_slashes=False)
def login():

    Handle user authentication.
    - GET: render login form
    - POST: validate credentials and start session

    error: str | None = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if check_auth(username, password):
            session["logged_in"] = True
            next_url = request.args.get("next")
            return redirect(next_url or url_for("go_to_demo_sheet"))
        else:
            error = "Invalid credentials"

    return render_template("needs_auth.html", error=error)
"""


@app.route("/logout", methods=["GET", "POST"])
def logout():
    """
    Log out the current user and clear the session.
    """
    session.clear()
    return redirect(url_for("home"))


@app.route("/admin")
@login_required
def admin():
    """
    Render the admin dashboard.
    """
    timestamps = myData.load_json(TIMESTAMP_PATH)
    try:
        demo_timestamp = timestamps.pop("demo")
    except Exception as e:
        demo_timestamp = "NO DATA: " + str(e)
    return render_template(
        "admin.html",
        groups_timestamps = timestamps,
        demo_timestamp = demo_timestamp
    )


@app.route("/updates-demos", methods=["POST"])
def update_demos():
    """
    Fetch the latest demo data from Google Sheets
    and update the local demos JSON file.
    """
    myExcel.update_demo_data(DEMO_SRC)
    myData.update_demos_timestamp(TIMESTAMP_PATH, iso_now_cet())
    return redirect(request.referrer or "/")


@app.route("/restart-tasks-10-days-old",
           methods=["POST"],
           strict_slashes=False)
def restart_tasks_10_days_or_older():
    """
    Resets data if the groups that have not updated their taks in 10 days.
    """
    data = myData.load_json(TIMESTAMP_PATH) or {}
    now = datetime.now(ZoneInfo("Europe/Madrid"))
    cutoff = now - timedelta(days=10)
    affected = 0
    for group_id, info in list(data.items()):
        last_time_str = info.get("last_time")
        if not last_time_str:
            continue
        try:
            last_time = datetime.fromisoformat(last_time_str)
        except ValueError:
            continue
        if last_time <= cutoff:
            restart_data_group(int(group_id))
            affected += 1
    return redirect(url_for("admin"))


def restart_data_group(group_id: int):
    """
    Reset specific group task files using the default task template.
    Deletes timestamp entry for that group.
    """
    filename = f"data{group_id:02d}.json"
    target_path = os.path.join(DATA_DIR, filename)
    shutil.copyfile(DATA_TEMPLATE, target_path)

    data = myData.load_json(TIMESTAMP_PATH) or {}
    data.pop(str(group_id), None)
    myData.atomic_write_json(TIMESTAMP_PATH, data)


@app.route("/restart-tasks-data", methods=["POST"], strict_slashes=False)
def restart_tasks_data():
    """
    Reset all group task files using the default task template.
    """
    for i in range(1, N_GROUPS + 1):
        restart_data_group(group_id=i)

    return redirect(url_for("admin"))


@app.route("/randomize-task-data", methods=["POST"], strict_slashes=False)
def randomize_task_data():
    """
    Randomly assign task statuses for all groups.

    Intended for testing and demo purposes.
    """
    myData.randomize_task_data(N_GROUPS, DATA_DIR)
    return redirect(url_for("admin"))


@app.route("/demos-sheet", strict_slashes=False)
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
    desc = getattr(error, 'description', "Access Error")
    return render_template(
        "base_error.html",
        title=f"{error.code} - Error",
        code=error.code,
        message="Unauthorized access",
        description=desc
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


def store_timestamp(data_path: str, group_id: int, counts: dict):
    """
    Stores ISO timestamp of group in data_path.
    counts contains a summary of the status requests
    """
    counts["last_time"] = iso_now_cet()
    data = myData.load_json(data_path)
    data[str(group_id)] = counts
    myData.atomic_write_json(data_path, data)


def iso_now_cet() -> str:
    """
    Return the current UTC time as an ISO-8601 string.
    Format example:
        2026-02-15T10:11:12Z
    Using UTC avoids timezone ambiguity and makes timestamps
    comparable across systems.
    """
    return datetime.now(ZoneInfo("Europe/Madrid")).isoformat()


def setup(n: int):
    N_GROUPS = n
    for i in range(1, N_GROUPS + 1):
        filename = f"data{str(i).zfill(2)}.json"
        target_path = os.path.join(DATA_DIR, filename)

        if not os.path.exists(target_path):
            shutil.copyfile(DATA_TEMPLATE, target_path)

    resolve_demo_data_endpoint(DEMO_SRC)
    myExcel.update_demo_data(DEMO_SRC)
    myData.update_demos_timestamp(TIMESTAMP_PATH, iso_now_cet())


if __name__ == "__main__":
    """
    Application entry point.

    Ensures all group task files exist before starting
    the Flask development server.
    """

    if len(sys.argv) > 1:
        try:
            N_GROUPS = int(sys.argv[1])
        except ValueError:
            print("INVALID ARGUMENT: " + sys.argv[1])
            N_GROUPS = 12
    app.run()


setup(N_GROUPS)