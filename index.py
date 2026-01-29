import xml.etree.ElementTree as ET
from flask import Flask, request, Response, render_template, jsonify
from datetime import datetime
import json
import os

ADMIN_USER = "admin"
ADMIN_PASS = "changeme"
DATA_DIR = "./data/"

app = Flask(__name__)

def check_auth(username, password):
    return username == ADMIN_USER and password == ADMIN_PASS

def authenticate():
    return Response(
        "Authentication required", 401,
        {"WWW-Authenticate": 'Basic realm="Admin Area"'}
    )

def requires_auth(f):
    def wrapper(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__  # important for Flask routing
    return wrapper

@app.route("/admin")
@requires_auth
def admin():
    groups = 3                      # number of groups
    tasks = [
        "Task one",
        "Task two",
        "Task three",
        "Task four",
        "Task five",
    ]
    return render_template(
        "admin.html",
        groups=groups,
        tasks=tasks
    )

def get_checklist_data(number):
    try:
        tree = ET.parse('data/data'+f'{number:02}'+'.xml')
        root = tree.getroot()
        # 1. Parse Metadata
        last_check = root.find('lastCheck').text if root.find('lastCheck') is not None else "N/A"
        # 2. Parse Zones and tasks
        zones = []
        for zone in root.findall('zone'):
            zone_data = {
                'title': zone.find('title').text,
                'tasks': []
            }
            for task in zone.findall('task'):
                task_data = {
                    'tarea': task.find('tarea').text,
                    'importancia': task.find('importancia').text,
                    'status': task.find('status').text
                }
                zone_data['tasks'].append(task_data)
            zones.append(zone_data)
            print(zone_data)

        # 3. Parse Footer Stats
        stats_node = root.find('data')
        stats = {}
        if stats_node is not None:
            stats = {
                'score': stats_node.find('Puntuacio').text,
                'percent': stats_node.find('percentatge').text,
                'total': stats_node.find('puntsTotals').text
            }

        return {
            'last_check': last_check,
            'zones': zones,
            'stats': stats
        }
    except Exception as e:
        print(f"XML Error: {e}")
        return None

def get_demo_data(group_number: int) -> dict:
    """
    Returns:
    {
      "group_name": "Grup X",
      "demos": ["task 1", "task 2", ...]
    }
    """
    JSON_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "./data/json/excel.json")
    )
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    group_name = f"Grup {group_number}"
    if group_name not in data:
        raise KeyError(f"Group not found: {group_name}")

    demos = [
        item[0]
        for item in data[group_name]
        if isinstance(item, list) and len(item) >= 1
    ]

    return {
        "group_name": group_name,
        "demos": demos
    }

@app.route('/')
def home():
    # Generate 16 groups for the dashboard
    groups = [f"{i:02d}" for i in range(1, 17)]
    return render_template('home.html', groups=groups)

@app.route('/group<number>')
def group_checklist(number):
    data = get_checklist_data(number)
    demo = get_demo_data(number)
    print(demo)
    return render_template('checklist.html', number=number, data=data, demo=demo)

if __name__ == '__main__':
    print("Server running at http://localhost:8000")
    app.run(port=8000, debug=True)
