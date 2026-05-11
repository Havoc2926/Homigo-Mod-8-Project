import bcrypt
import bleach
import psycopg2
from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response, abort, session, flash, get_flashed_messages
import requests
import json
import os
from psycopg2 import pool
from functools import wraps


GOVEE_API_KEY = "change-me"
SCENE_FILE = 'scenes.json'
db_pool = psycopg2.pool.SimpleConnectionPool(1, 10, host='bronto.ewi.utwente.nl', port=5432, user='username-here', password='change-me', dbname='dbname-here')

spotifyAPI = "change-me"
app = Flask(__name__)
app.secret_key = "change-me"


#PYTHON FUNCTIONS!!

def get_govee_lights():
    headers = {
        "Govee-API-Key": GOVEE_API_KEY
    }
    response = requests.get("https://developer-api.govee.com/v1/devices", headers=headers)
    if response.status_code == 200:
        devices = response.json().get("data", {}).get("devices", [])
        return [
            {"device": d["device"], "name": d["deviceName"], "model": d["model"]}
            for d in devices
        ]
    return []

def load_scenes():
    if not os.path.exists(SCENE_FILE):
        return {"happy": {}, "focus": {}, "party": {}}
    with open(SCENE_FILE, 'r') as f:
        return json.load(f)

def save_scenes(scenes):
    with open(SCENE_FILE, 'w') as f:
        json.dump(scenes, f, indent=4)

def hex_to_rgb(hex_color):
    """Convert hex (#RRGGBB) to RGB dict"""
    hex_color = hex_color.lstrip("#")
    return {
        "r": int(hex_color[0:2], 16),
        "g": int(hex_color[2:4], 16),
        "b": int(hex_color[4:6], 16)
    }

def set_scene(scene_name):
    # Load scenes
    with open(SCENE_FILE, "r") as f:
        scenes = json.load(f)
    scene = scenes.get(scene_name, {})
    if not scene:
        return {"error": "Scene not found or empty"}, 404

    # Load device list (for model info)
    lights = get_govee_lights()  # uses Govee API
    model_lookup = {d["device"]: d["model"] for d in lights}

    results = []
    for device_id, hex_color in scene.items():
        rgb = hex_to_rgb(hex_color)
        model = model_lookup.get(device_id, "")

        payload = {
            "device": device_id,
            "model": model,
            "cmd": {
                "name": "color",
                "value": rgb
            }
        }
        headers = {
            "Govee-API-Key": GOVEE_API_KEY,
            "Content-Type": "application/json"
        }

        response = requests.put(
            "https://developer-api.govee.com/v1/devices/control",
            headers=headers,
            json=payload
        )

        results.append({
            "device": device_id,
            "status": response.status_code,
            "response": response.text
        })

    return {"message": f"Scene '{scene_name}' triggered", "results": results}, 200

#APP ROUTES BELOW!!


def get_db_connection():
    try:
        return db_pool.getconn()
    except psycopg2.Error as e:
        print(f"Error getting connection from pool: {e}")
        return None


def release_db_connection(conn):
    try:
        db_pool.putconn(conn)
    except psycopg2.Error as e:
        print(f"Error releasing connection to pool: {e}")
@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get('user')
        if not user or 'email' not in user:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/dashboard')
@login_required

def dashboard():
    return render_template('index.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = bleach.clean(request.form.get('name', '') or '')
        email = bleach.clean(request.form.get('email'))
        password = bleach.clean(request.form.get('password'))
        salt = bcrypt.gensalt()

        secure_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                sql = """
INSERT INTO "homigo"."User"("EmailAddress", "Name", "password", "salt", "lightAPI", "spotifyAPI")
VALUES (CAST(%s AS VARCHAR), CAST(%s AS VARCHAR), CAST(%s AS VARCHAR), CAST(%s AS VARCHAR), CAST(%s AS VARCHAR), CAST(%s AS VARCHAR));                """

                cur.execute(sql, ( email,name, secure_password.decode('utf-8'), salt.decode('utf-8'),GOVEE_API_KEY,spotifyAPI))
                conn.commit()

            finally:
                cur.close()
                release_db_connection(conn)

        return render_template('login.html')
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:  # User is already logged in
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = bleach.clean(request.form.get('email'))
        password = bleach.clean(request.form.get('password'))

        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                sql = """
                SELECT "password", "salt"
                FROM "homigo"."User"
                WHERE "EmailAddress" = CAST(%s AS VARCHAR);
                """
                cur.execute(sql, (email,))
                result = cur.fetchone()

                if result:
                    stored_hash_str, salt_str = result

                    # Convert both to bytes
                    stored_hash = stored_hash_str.encode('utf-8')
                    salt = salt_str.encode('utf-8')

                    entered_hash = bcrypt.hashpw(password.encode('utf-8'), salt)

                    if entered_hash == stored_hash:
                        session.permanent = True
                        session['user'] = {'email': email}
                        return redirect(url_for('dashboard'))
                    else:
                        error = "Inv"
                        return render_template('login.html', error=error)
                else:
                    error = "Invalid username or password"
                    return render_template('login.html', error=error)
            finally:
                cur.close()
                release_db_connection(conn)
        else:
            error = "An unexpected error occurred"
            return render_template('login.html', error=error)

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()  # Remove all session data
    return redirect(url_for('login'))


@app.route('/lights')
def getLights():
    return jsonify(get_govee_lights())

@app.route('/api/scenes', methods=['GET'])
def getScenes():
    return jsonify(load_scenes())

@app.route('/api/scenes', methods=['POST'])
def update_scene():
    data = request.json
    scene_name = data.get("name")
    colors = data.get("colors")

    if scene_name not in ["happy", "focus", "party"]:
        return jsonify({"error": "Invalid scene name"}), 400

    if not isinstance(colors, dict):
        return jsonify({"error": "Invalid colors format"}), 400

    scenes = load_scenes()
    scenes[scene_name] = colors
    save_scenes(scenes)

    return jsonify({"message": f"Scene '{scene_name}' updated successfully"})


@app.route('/api/trigger/<scene_name>', methods=['GET'])
def triggerScene(scene_name):
    if scene_name not in ["happy", "focus", "party"]:
        return jsonify({"error": "Invalid scene name"}), 400

    result, status = set_scene(scene_name)
    return jsonify(result), status

if __name__ == '__main__':
    app.run(debug=True)
