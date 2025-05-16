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

@app.route("/playlists")
def get_playlists():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, service_name, countries, main_categories, epg_url, github_epg_url, timestamp, donation_info FROM playlists")
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
