from flask import Flask, request, send_file, render_template, jsonify
from flask_cors import CORS
from flask_compress import Compress
from db import get_connection
from datetime import datetime
from mailing import newList_email, updatedList_email
import requests
import re
import io
import os
import logging
import sys
import bcrypt



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
DB_TABLE = 'playlists'
DRIVE_FILES_TABLE = 'drive_files'

SERVICE_ACCOUNT_FILE = os.path.join(os.getcwd(), "")
SCOPES = ['https://www.googleapis.com/auth/drive']

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build('drive', 'v3', credentials=credentials)

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

def process_m3u_file(filepath, dns, username, password):

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
                    placeholder_url = f"http://{dns}/{username}/{password}/{stream_id}\n"
                    new_lines.append(placeholder_url)
                else:
                    placeholder_url = f"http://{dns}/{content_type}/{username}/{password}/{stream_id}\n"
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
    list_password = bcrypt.hashpw(list_password.encode(), bcrypt.gensalt())

    try:
        temp_filename = "temp_uploaded.m3u"
        temp_path = os.path.join(UPLOAD_FOLDER, temp_filename)
        file.save(temp_path)

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT MAX(id) FROM {DB_TABLE} ")
        result = cursor.fetchone()
        max_id = result['MAX(id)'] if result and result['MAX(id)'] is not None else 0

        playlist_id = max_id + 1
        current_path = os.getcwd()

        cursor.execute(f"""
            INSERT INTO {DB_TABLE}  (service_name, countries, reddit_user, main_categories, epg_url, donation_info, owner_password_hash, timestamp, m3u_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, '')
        """, (service_name, countries, reddit_username, main_categories, epg, donation_link, list_password, datetime.today().strftime('%d/%m/%Y')))
        conn.commit()
        temp_playlist_id = cursor.lastrowid

        if not os.path.exists(temp_path):
            logging.error(f"El archivo temporal no existe: {temp_path}")
        else:
            logging.info(f"Archivo temporal encontrado: {temp_path}")

        process_m3u_file(temp_path, "DNS", "USERNAME", "PASSWORD")

        final_filename = f"{playlist_id}.m3u"
        final_path = os.path.join(UPLOAD_FOLDER, final_filename)

        os.rename(temp_path, final_path)

        if os.path.exists(final_path):
            logging.info(f"Archivo final ya existe y será sobrescrito: {final_path}")
        else:
            logging.info(f"No existe archivo final, se creará: {final_path}")

        cursor.execute(f"UPDATE {DB_TABLE}  SET m3u_url = %s WHERE id = %s", (final_path, temp_playlist_id))
        conn.commit()
        cursor.execute(f"UPDATE {DB_TABLE}  SET id = %s WHERE id = %s", (playlist_id, temp_playlist_id))
        conn.commit()

        cursor.close()
        conn.close()

        Details = f"""Servicio: {service_name} 
        Paises: {countries}
        Usuario: {reddit_username}
        Categorias: {main_categories}"""

        newList_email(Details)

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


    form_data = request.form.to_dict()

    valid_fields = {
        k: v.strip() for k, v in form_data.items()
        if k not in required_fields and v.strip()
    }

    playlist_id = request.form['id']
    list_password = request.form['list_password']

    try:
        temp_filename = "temp_uploaded.m3u"
        temp_path = os.path.join(UPLOAD_FOLDER, temp_filename)
        file.save(temp_path)

        logging.info(f"Llegamos hasta la creacion del fichero temporal?")        

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        logging.info(f"Llegamos hasta antes de la llamada SELECT")
        cursor.execute(f"SELECT owner_password_hash FROM {DB_TABLE}  WHERE id = %s", (playlist_id,))
        logging.info(f"Llegamos hasta despues de la llamada SELECT")
        result = cursor.fetchone()
        DB_list_password = result['owner_password_hash'].encode()

        if not bcrypt.checkpw(list_password.encode(), DB_list_password):
            return jsonify({"error": "password is not correct"}), 500

        current_path = os.getcwd()

        cursor.execute(f"UPDATE {DB_TABLE}  SET timestamp = %s WHERE id = %s", (datetime.today().strftime('%d/%m/%Y'), playlist_id))
        conn.commit()

        set_clause = ', '.join(f"{k} = %s" for k in valid_fields)
        values = list(valid_fields.values())

        if valid_fields:
            sql = f"UPDATE {DB_TABLE} SET {set_clause} WHERE id = %s"
            values.append(playlist_id)

            cursor.execute(sql, values)
            conn.commit()

        cursor.close()
        conn.close()
        logging.info(f"Llegamos hasta despues de la llamada de UPDATE")

        if not os.path.exists(temp_path):
            logging.error(f"El archivo temporal no existe: {temp_path}")
        else:
            logging.info(f"Archivo temporal encontrado: {temp_path}")

        process_m3u_file(temp_path, "DNS", "USERNAME", "PASSWORD")

        final_filename = f"{playlist_id}.m3u"
        final_path = os.path.join(UPLOAD_FOLDER, final_filename)

        os.rename(temp_path, final_path)

        if os.path.exists(final_path):
            logging.info(f"Archivo final ya existe y será sobrescrito: {final_path}")
        else:
            logging.info(f"No existe archivo final, se creará: {final_path}")

        Details = f"""ID: {playlist_id}
         """

        update_AssociatedLists(playlist_id)

        updatedList_email(Details)

        return jsonify({"message": "Playlist uploaded successfully", "playlist_id": playlist_id, "m3u_url": final_path})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def update_AssociatedLists(playlist_id: str) -> None:
    """
    Recupera todos los drive_file_id que correspondan a playlist_id y
    actualiza su contenido en Drive con el .m3u final que tienes en UPLOAD_FOLDER.
    """
    # 1) Path del .m3u que acabas de generar en update_playlist()
    final_filename = f"{playlist_id}.m3u"
    file_path = os.path.join(UPLOAD_FOLDER, final_filename)

    if not os.path.exists(file_path):
        logging.error("No existe el fichero local a subir: %s", file_path)
        return

    # 2) Recuperar todos los drive_file_id asociados
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT drive_file_id FROM {DRIVE_FILES_TABLE} WHERE list_id = %s",
        (playlist_id,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        logging.info("No hay ficheros en drive asociados a la lista %s", playlist_id)
        return

    # 3) Prepara el media upload para el .m3u
    media = MediaFileUpload(
        file_path,
        mimetype='application/octet-stream',  # o 'application/x-mpegURL'
        resumable=False
    )

    # 4) Itera y actualiza
    for (drive_file_id,) in rows:
        try:
            updated = drive_service.files().update(
                fileId=drive_file_id,
                media_body=media
            ).execute()
            logging.info(
                "Actualizado en Drive: playlist_id=%s → fileId=%s, mimeType=%s",
                playlist_id, updated.get('id'), updated.get('mimeType')
            )
        except Exception as e:
            logging.exception(
                "Error actualizando en Drive fileId=%s para playlist_id=%s",
                drive_file_id, playlist_id
            )

@app.route('/api/files', methods=['POST'])
def save_file_record():

    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    list_id        = data.get('list_ID') or data.get('list_id')
    drive_file_id  = data.get('drive_file_id')
    filename       = data.get('filename')  # opcional

    if not list_id:
        return jsonify({"error": "Missing field list_ID/list_id"}), 400
    if not drive_file_id:
        return jsonify({"error": "Missing field drive_file_id"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            f"SELECT id FROM {DRIVE_FILES_TABLE} WHERE list_id = %s",
            (list_id,)
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                f"""
                UPDATE {DRIVE_FILES_TABLE}
                   SET drive_file_id = %s,
                       uploaded_at    = %s
                 WHERE list_id       = %s
                """,
                (drive_file_id, datetime.now(), list_id)
            )
            record_id = existing['id']
            action = 'updated'
        else:
            cursor.execute(
                f"""
                INSERT INTO {DRIVE_FILES_TABLE}
                    (list_id, drive_file_id, uploaded_at)
                VALUES
                    (%s,      %s,            %s)
                """,
                (list_id, drive_file_id, datetime.now())
            )
            record_id = cursor.lastrowid
            action = 'created'

        conn.commit()
        cursor.close()
        conn.close()

        logging.info(f"Drive‐record {action}: list_id={list_id}, drive_file_id={drive_file_id}")

        return jsonify({
            "success"      : True,
            "action"       : action,
            "record_id"    : record_id,
            "list_id"      : list_id
        }), 201

    except Exception as e:
        logging.exception("Error saving drive_file record")
        return jsonify({"error": str(e)}), 500

@app.route("/playlists")
def get_playlists():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(f"SELECT id, reddit_user, service_name, countries, main_categories, epg_url, github_epg_url, timestamp, clicks, donation_info FROM {DB_TABLE}  WHERE display = 1")

    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(data)

@app.route('/manual', methods=['POST'])
def manual():
    data = request.json
    id_selected = data['id']

    db = get_connection()
    cursor = db.cursor()
    cursor.execute(f"SELECT m3u_url FROM {DB_TABLE}  WHERE id = %s", (id_selected,))
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

    cursor.execute(f"UPDATE {DB_TABLE} SET clicks = clicks + 1 WHERE id = %s", (id_selected,))
    
    db.commit()
    cursor.close()
    db.close()
    
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
    cursor.execute(f"SELECT m3u_url FROM {DB_TABLE}  WHERE id = %s", (id_selected,))
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

    
    content = re.sub(r'(?i)(?<!http://)(dns)', r'http://\1', content)
    
    content = re.sub(r'\bDNS\b', dns, content, flags=re.IGNORECASE)
    content = re.sub(r'\bUSERNAME\b', username, content, flags=re.IGNORECASE)
    content = re.sub(r'\bPASSWORD\b', password, content, flags=re.IGNORECASE)

    output = io.BytesIO()
    output.write(content.encode('utf-8'))
    output.seek(0)

    filename = f"modified_playlist_{id_selected}.m3u"

    cursor.execute(f"UPDATE {DB_TABLE} SET clicks = clicks + 1 WHERE id = %s", (id_selected,))
    
    db.commit()
    cursor.close()
    db.close()

    return send_file(
        output,
        mimetype='audio/x-mpegurl',
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
