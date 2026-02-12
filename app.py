from flask import Flask, request, Response, redirect, render_template, send_from_directory
from datetime import datetime, timedelta
from flask import Blueprint, send_file, current_app, jsonify
from pathlib import Path
import scripts.myData as myData
import scripts.badges as badges
import json, sys, os


N_GROUPS = 12


app = Flask(__name__)
tasks_bp = Blueprint("tasks", __name__, url_prefix="/api")

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/api/update-tasks")
def submit():
    group_id = request.args.get("group_id", "")
    if not group_id:
        return jsonify({"error": "Missing group_id query param"}), 400

    if not re.fullmatch(r"\d+", group_id):
        return jsonify({"error": "group_id must be numeric"}), 400

    gid = str(int(group_id)).zfill(2)  # "7" -> "07", "07" -> "07"
    payload = request.get_json(silent=True)

    if payload is None:
        return jsonify({"error": "Request body must be JSON"}), 400

    out_path = DATA_DIR / f"data{gid}.json"

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return jsonify({"ok": True, "saved_as": str(out_path), "group_id": gid}), 200



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
    groups = [f"{i:02d}" for i in range(1, N_GROUPS + 1) ]
    return render_template('home.html', groups=groups)

@app.route("/test")
def test():
    return render_template("test.html")


@app.route("/echo", methods=["POST"])
def echo():
    # simple test endpoint
    from flask import request
    return request.json, 200


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

app.register_blueprint(tasks_bp)

USERNAME = "admin"
PASSWORD = "admin123"

def check_auth(username, password):
    return username == USERNAME and password == PASSWORD

def authenticate():
    return Response(
        "Authentication required",
        401,
        {"WWW-Authenticate": 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

@app.route("/admin")
@requires_auth
def goToDemos():
    return redirect("https://docs.google.com/spreadsheets/d/1cma0J7eTugMeRtG8VCHbYiHb5RlJ6TLK_SPYUoxfDFA/edit?usp=sharing")


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
        description="We're experiencing technical difficulties. Please try again later."
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
    app.run()

