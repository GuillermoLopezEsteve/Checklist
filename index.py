import xml.etree.ElementTree as ET
from flask import Flask, request, Response


ADMIN_USER = "admin"
ADMIN_PASS = "changeme" 


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
    return "hello admin"



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

@app.route('/')
def home():
    # Generate 16 groups for the dashboard
    groups = [f"{i:02d}" for i in range(1, 17)]
    return render_template('home.html', groups=groups)

@app.route('/group<number>')
def group_checklist(number):
    data = get_checklist_data(number)
    return render_template('checklist.html', number=number, data=data)

if __name__ == '__main__':
    print("Server running at http://localhost:8000")
    app.run(port=8000, debug=True)