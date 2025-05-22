from flask import Flask, request, send_file, render_template, jsonify
from flask_cors import CORS
from flask_compress import Compress
from db import get_connection
from datetime import datetime
import requests
import re
import io
import os
import logging
import sys



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

UPLOAD_FOLDER = os.path.join(os.getcwd(), "playlists")
ALLOWED_EXTENSIONS = {'m3u'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    stream=sys.stdout
)

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
    return content_type or 'live' 

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
                url_split = url_line.split("/")
                stream_id = url_split[len(url_split) - 1]

                if '/live/' in url_line:
                    content_type = 'live'
                elif '/movie/' in url_line:
                    content_type = 'movie'
                elif '/series/' in url_line:
                    content_type = 'series'
                else:
                    content_type = ''

                if content_type == '':
                    placeholder_url = f"http://{dns}/USERNAME/PASSWORD/{stream_id}\n"
                    new_lines.append(placeholder_url)
                else:
                    placeholder_url = f"http://{dns}/{content_type}/USERNAME/PASSWORD/{stream_id}\n"
                    new_lines.append(placeholder_url)

                i += 2
                continue

        i += 1

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        logging.info(f"Archivo guardado correctamente en: {filepath}")
    except Exception as e:
        logging.error(f"Error al guardar el archivo: {e}")


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
        cursor.execute("SELECT MAX(id) FROM test_playlists")
        result = cursor.fetchone()
        max_id = result['MAX(id)'] if result and result['MAX(id)'] is not None else 0

        playlist_id = max_id + 1
        current_path = os.getcwd()

        cursor.execute("""
            INSERT INTO test_playlists (service_name, countries, reddit_user, main_categories, epg_url, donation_info, owner_password_hash, timestamp, m3u_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, '')
        """, (service_name, countries, reddit_username, main_categories, epg, donation_link, list_password, datetime.today().strftime('%d-%m-%Y')))
        conn.commit()
        temp_playlist_id = cursor.lastrowid

        if not os.path.exists(temp_path):
            logging.error(f"El archivo temporal no existe: {temp_path}")
        else:
            logging.info(f"Archivo temporal encontrado: {temp_path}")

        process_m3u_file(temp_path, "DNS")

        final_filename = f"{playlist_id}.m3u"
        final_path = os.path.join(UPLOAD_FOLDER, final_filename)

        os.rename(temp_path, final_path)

        if os.path.exists(final_path):
            logging.info(f"Archivo final ya existe y será sobrescrito: {final_path}")
        else:
            logging.info(f"No existe archivo final, se creará: {final_path}")

        cursor.execute("UPDATE test_playlists SET m3u_url = %s WHERE id = %s", (final_path, temp_playlist_id))
        conn.commit()
        cursor.execute("UPDATE test_playlists SET id = %s WHERE id = %s", (playlist_id, temp_playlist_id))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "Playlist uploaded successfully", "playlist_id": playlist_id, "m3u_url": final_path})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update_playlist', methods=['POST'])
def update_playlist():
    required_fields = ['id', 'list_password']
    for field in required_fields:
        if field not in request.form:
            return jsonify({"error": f"Missing field {field}"}), 400

    file = request.files.get('m3u_file')
    if not file:
        return jsonify({"error": "No file uploaded"}), 400
    if not file.filename.endswith('.m3u'):
        return jsonify({"error": "File must be .m3u"}), 400

    playlist_id = request.form['id']
    list_password = request.form['list_password']

    try:
        temp_filename = "temp_uploaded.m3u"
        temp_path = os.path.join(UPLOAD_FOLDER, temp_filename)
        file.save(temp_path)

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT owner_password_hash FROM test_playlists WHERE id = %s", (playlist_id))
        DB_list_password = cursor.fetchone()['owner_password_hash']
        if(DB_list_password != list_password):
            return jsonify({"error": str(e)}), 500

        current_path = os.getcwd()

        cursor.execute("UPDATE test_playlists SET timestamp = %s WHERE id = %s", (datetime.today().strftime('%d-%m-%Y'), playlist_id))
        conn.commit()
        cursor.close()
        conn.close()

        if not os.path.exists(temp_path):
            logging.error(f"El archivo temporal no existe: {temp_path}")
        else:
            logging.info(f"Archivo temporal encontrado: {temp_path}")

        process_m3u_file(temp_path, "DNS")

        final_filename = f"{playlist_id}.m3u"
        final_path = os.path.join(UPLOAD_FOLDER, final_filename)

        os.rename(temp_path, final_path)

        if os.path.exists(final_path):
            logging.info(f"Archivo final ya existe y será sobrescrito: {final_path}")
        else:
            logging.info(f"No existe archivo final, se creará: {final_path}")

        return jsonify({"message": "Playlist uploaded successfully", "playlist_id": playlist_id, "m3u_url": final_path})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/playlists")
def get_playlists():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, service_name, countries, main_categories, epg_url, github_epg_url, timestamp, donation_info FROM test_playlists WHERE display = 1")

    cursor.close()
    conn.close()

    return jsonify(data)

@app.route('/manual', methods=['POST'])
def manual():
    data = request.json
    id_selected = data['id']

    db = get_connection()
    cursor = db.cursor()
    cursor.execute("SELECT m3u_url FROM test_playlists WHERE id = %s", (id_selected,))
    row = cursor.fetchone()

    if not row:
        return "Playlist not found", 404

    m3u_path = row[0]

    if not os.path.exists(m3u_path):
        current_path = os.getcwd()
        return jsonify({
            "error": "File not found on server",
            "path": m3u_path
        }), 404

    try:
        with open(m3u_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return f"File read error: {str(e)}", 500
    
    output = io.BytesIO()
    output.write(content.encode('utf-8'))
    output.seek(0)

    filename = f"raw_playlist_{id_selected}.m3u"

    return send_file(
        output,
        mimetype='audio/x-mpegurl',
        as_attachment=True,
        download_name=filename
    )

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    id_selected = data['id']
    dns = data['dns']
    username = data['username']
    password = data['password']

    db = get_connection()
    cursor = db.cursor()
    logging.info(f"Archivo final ya existe y será sobrescrito: {id_selected}")
    cursor.execute("SELECT m3u_url FROM test_playlists WHERE id = %s", (id_selected,))
    row = cursor.fetchone()
    logging.info(f"Archivo final ya existe y será sobrescrito: {row}")


    if not row:
        return "Playlist not found", 404

    m3u_path = row[0]

    if not os.path.exists(m3u_path):
        current_path = os.getcwd()
        return jsonify({
            "error": "File not found on server",
            "path": m3u_path
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
