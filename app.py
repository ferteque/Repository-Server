from flask import Flask, request, send_file, render_template, jsonify
from flask_cors import CORS
from flask_compress import Compress
from db import get_connection
import requests
import re
import io
import os

app = Flask(__name__)
Compress(app)  
CORS(app, resources={r"/process": {"origins": [
    "https://repository-server.onrender.com",
    "https://striking-orella-ferteque-e35fe763.koyeb.app", 
    "https://repo-server.site"
]}})

@app.route('/')
def home():
    return render_template("index.html") 

UPLOAD_FOLDER = '/playlists'
ALLOWED_EXTENSIONS = {'m3u'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_content_type(filepath):
    content_type = None
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if line.startswith('#EXTINF'):
            if i + 1 < len(lines):
                url_line = lines[i + 1].strip()
                if '/live/' in url_line:
                    content_type = 'live'
                    break
                elif '/movie/' in url_line:
                    content_type = 'movie'
                    break
                elif '/series/' in url_line:
                    content_type = 'series'
                    break
    return content_type or 'live'  # default

def process_m3u_file(filepath, dns):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)

        if line.startswith('#EXTINF'):
            if i + 1 < len(lines):
                url_line = lines[i + 1].strip()

                if '/live/' in url_line:
                    content_type = 'live'
                elif '/movie/' in url_line:
                    content_type = 'movie'
                elif '/series/' in url_line:
                    content_type = 'series'
                else:
                    content_type = ''

                if content_type == '':
                    placeholder_url = f"http://{dns}/USERNAME/PASSWORD/840009\n"
                    new_lines.append(placeholder_url)
                else:
                    placeholder_url = f"http://{dns}/{content_type.upper()}/USERNAME/PASSWORD/840009\n"
                    new_lines.append(placeholder_url)

                i += 2  # Saltamos la línea de URL original, porque ya la sustituimos
                continue

        i += 1

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

@app.route('/upload_playlist', methods=['POST'])
def upload_playlist():
    required_fields = ['service_name', 'countries', 'reddit_username', 'main_categories', 'epg', 'donation_link', 'list_password']
    for field in required_fields:
        if field not in request.form:
            return jsonify({"error": f"Missing field {field}"}), 400

    file = request.files.get('m3u_file')
    if not file:
        return jsonify({"error": "No file uploaded"}), 400
    if not file.filename.endswith('.m3u'):
        return jsonify({"error": "File must be .m3u"}), 400

    service_name = request.form['service_name']
    countries = request.form['countries']
    reddit_username = request.form['reddit_username']
    main_categories = request.form['main_categories']
    epg = request.form['epg']
    donation_link = request.form['donation_link']
    list_password = request.form['list_password']

    try:
        temp_filename = "temp_uploaded.m3u"
        temp_path = os.path.join(UPLOAD_FOLDER, temp_filename)
        file.save(temp_path)

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT MAX(id) FROM playlists")
        result = cursor.fetchone()
        max_id = result['MAX(id)'] if result and result['MAX(id)'] is not None else 0

        playlist_id = max_id + 1
        current_path = os.getcwd()
        print(current_path)
        cursor.execute("""
            INSERT INTO playlists (service_name, countries, reddit_user, main_categories, epg_url, donation_info, owner_password_hash, m3u_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, '')
        """, (service_name, countries, reddit_username, main_categories, epg, donation_link, list_password))
        conn.commit()
        temp_playlist_id = cursor.lastrowid

        process_m3u_file(temp_path, "DNS")

        final_filename = f"{playlist_id}.m3u"
        final_path = os.path.join(UPLOAD_FOLDER, final_filename)
        os.rename(temp_path, final_path)

        m3u_url = f"./playlists/{final_filename}"
        cursor.execute("UPDATE playlists SET m3u_url = %s WHERE id = %s", (m3u_url, temp_playlist_id))
        cursor.execute("UPDATE playlists SET id = %s WHERE id = %s", (playlist_id, temp_playlist_id))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "Playlist uploaded successfully", "playlist_id": playlist_id, "m3u_url": m3u_url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/playlists")
def get_playlists():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, service_name, reddit_user, countries, main_categories, epg_url, github_epg_url, timestamp, donation_info FROM playlists WHERE display = 1")
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(data)

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    id_selected = data['id']
    dns = data['dns']
    username = data['username']
    password = data['password']

    db = get_connection()
    cursor = db.cursor()
    cursor.execute("SELECT m3u_url FROM playlists WHERE id = %s", (id_selected,))
    row = cursor.fetchone()

    if not row:
        return "Playlist not found", 404

    m3u_path = row[0]

    if not os.path.exists(m3u_path):
        current_path = os.getcwd()
        return jsonify({
            "error": "File not found on server",
            "path": m3u_path,
            "current": current_path
        }), 404

    try:
        with open(m3u_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return f"File read error: {str(e)}", 500

    
    content = re.sub(r'(?<!http://)(DNS)', r'http://\1', content)
    content = re.sub(r'(?<!http://)(dns)', r'http://\1', content)

    
    content = re.sub(r'\bDNS\b', dns, content, flags=re.IGNORECASE)
    content = re.sub(r'\bUSERNAME\b', username, content, flags=re.IGNORECASE)
    content = re.sub(r'\bPASSWORD\b', password, content, flags=re.IGNORECASE)

    output = io.BytesIO()
    output.write(content.encode('utf-8'))
    output.seek(0)

    filename = f"modified_playlist_{id_selected}.m3u"

    return send_file(
        output,
        mimetype='audio/x-mpegurl',
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
