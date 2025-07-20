from flask import Flask, request, send_file, render_template, jsonify, make_response
from flask_cors import CORS
from flask_compress import Compress
from db import get_connection
from datetime import datetime
from mailing import newList_email, updatedList_email
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from urllib.parse import urlparse
from threading import Thread
import shutil
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
def index():
    return render_template('index.html')

@app.after_request
def set_csp(response):
    response.headers['Content-Security-Policy-Report-Only'] = (
        "default-src 'self'; "
        "script-src 'self' https://apis.google.com https://cdn.jsdelivr.net https://www.googletagmanager.com https://accounts.google.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "font-src 'self' https://fonts.gstatic.com; "
        "media-src 'self'; "
        "img-src 'self' data:; "
        "connect-src 'self' https://region1.google-analytics.com; "
    )
    return response

UPLOAD_FOLDER = os.path.join(os.getcwd(), "playlists")
ALLOWED_EXTENSIONS = {'m3u'}
DB_TABLE = 'playlists'
DRIVE_FILES_TABLE = 'drive_files'

SERVICE_ACCOUNT_FILE = os.path.join(os.getcwd(), "service-account.json")
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

def process_m3u_file(filepath, dns, username, password):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    group_titles = set()
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)

        if line.startswith('#EXTINF'):
            match = re.search(r'group-title="(.*?)"', line)
            if match:
                group_titles.add(match.group(1).strip())  
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
        return group_titles
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

        group_titles = process_m3u_file(temp_path, "DNS", "USERNAME", "PASSWORD")

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

        for group_name in group_titles:
            try:
                logging.info(f"Group name: {group_name}")
                cursor.execute(
                    "INSERT INTO categories (list_id, name, auto_update) VALUES (%s, %s, %s)",
                    (playlist_id, group_name, 0)
                )
            except mysql.connector.Error as e:
                logging.error(f"Error inserting group '{group_name}': {e}")

        conn.commit()
        

        
        cursor.execute("SELECT id, name FROM categories WHERE list_id = %s", (playlist_id,))
        groups = cursor.fetchall()

        logging.info(f"Llegamos hasta despues del fetchall?")

        cursor.close()
        conn.close()

        Details = f"""Servicio: {service_name} 
        Paises: {countries}
        Usuario: {reddit_username}
        Categorias: {main_categories}"""

        newList_email(Details)



        try:
            return jsonify({
                "message": "Playlist uploaded successfully",
                "playlist_id": playlist_id,
                "m3u_url": final_path,
                "groups": [{'id': row['id'], 'name': row['name']} for row in groups]
            })
        except Exception as e:
            logging.exception("Error serializing response for groups")
            return jsonify({"error": "Error processing response", "details": str(e)}), 500

    except Exception as e:
        return jsonify({"error": "str(e)"}), 500

@app.route('/save_selected_groups', methods=['POST'])
def save_selected_groups():
    data = request.get_json()

    group_ids = data.get('group_ids', [])

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        for group_id in group_ids:
            cursor.execute(
                "UPDATE categories SET auto_update = 1 WHERE id = %s",
                (group_id,)
            )

        logging.info(f"Llegamos hasta despues del execute?")

        conn.commit()

        logging.info(f"Llegamos hasta despues del commit?")
        cursor.close()
        conn.close()

        return jsonify({'message': 'Categories successfully created'})

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': 'Error when saving categories'}), 500


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
        
        group_titles = process_m3u_file(temp_path, "DNS", "USERNAME", "PASSWORD")
        cursor.execute("SELECT name FROM categories WHERE list_id = %s", (playlist_id,))
        existing_categories = set(row[0] for row in cursor.fetchall())

        new_categories = set(group_titles)

        categories_to_delete = existing_categories - new_categories

        categories_to_insert = new_categories - existing_categories

        for category in categories_to_delete:
            cursor.execute(
                "DELETE FROM categories WHERE list_id = %s AND name = %s",
                (playlist_id, category)
            )

        for category in categories_to_insert:
            try:
                cursor.execute(
                    "INSERT INTO categories (list_id, name, auto_update) VALUES (%s, %s, %s)",
                    (playlist_id, category, 0)
                )
            except mysql.connector.Error as e:
                logging.error(f"Error inserting group '{category}': {e}")

        conn.commit()
        

        
        cursor.execute("SELECT id, name,auto_update FROM categories WHERE list_id = %s", (playlist_id,))
        groups = cursor.fetchall()

        cursor.close()
        conn.close()
        logging.info(f"Llegamos hasta despues de la llamada de UPDATE")

        if not os.path.exists(temp_path):
            logging.error(f"El archivo temporal no existe: {temp_path}")
        else:
            logging.info(f"Archivo temporal encontrado: {temp_path}")

        

        final_filename = f"{playlist_id}.m3u"
        final_path = os.path.join(UPLOAD_FOLDER, final_filename)

        os.rename(temp_path, final_path)

        if os.path.exists(final_path):
            logging.info(f"Archivo final ya existe y será sobrescrito: {final_path}")
        else:
            logging.info(f"No existe archivo final, se creará: {final_path}")

        Details = f"""ID: {playlist_id}
         """

        thread = Thread(
        target=update_AssociatedLists,
        args=(playlist_id,),
        daemon=True        
        )
        thread.start()

        updatedList_email(Details)

        try:
            return jsonify({
                "message": "Playlist updated successfully",
                "playlist_id": playlist_id,
                "m3u_url": final_path,
                "groups": [{'id': row['id'], 'name': row['name'], 'auto_update': row['auto_update']} for row in groups]
            })
        except Exception as e:
            logging.exception("Error serializing response for groups")
            return jsonify({"error": "Error processing response", "details": str(e)}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def update_AssociatedLists(playlist_id: str) -> None:
    """
    Recupera todos los drive_file_id que correspondan a playlist_id y
    actualiza su contenido en Drive con el .m3u final que tienes en UPLOAD_FOLDER.
    """
    # 1) Path del .m3u que acabas de generar en update_playlist()
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT drive_file_id FROM {DRIVE_FILES_TABLE} WHERE list_id = %s and valid=1",
        (playlist_id,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        logging.info("No hay ficheros Drive para playlist %s", playlist_id)
        return

    # 2) Ruta de tu fichero local ya actualizado
    local_updated = os.path.join(UPLOAD_FOLDER, f"{playlist_id}.m3u")
    if not os.path.exists(local_updated):
        logging.error("Fichero local actualizado no existe: %s", local_updated)
        return

    for (drive_file_id,) in rows:
        try:
            # ----- 3) Descarga remota solo para extraer credenciales -----
            req = drive_service.files().get_media(fileId=drive_file_id)
            buf = io.BytesIO()
            downloader = MediaIoBaseDownload(buf, req)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            buf.seek(0)

            # vuelca a lista de líneas
            remote_lines = buf.read().decode('utf-8', errors='ignore').splitlines()
            if len(remote_lines) < 3:
                logging.error("El remoto no tiene 3 líneas: %s", drive_file_id)
                continue

            raw_url = remote_lines[2].strip()
            p = urlparse(raw_url)
            dns = p.netloc
            segs = p.path.strip('/').split('/')

            if len(segs) >= 4:
                user, pwd = segs[1], segs[2]
            elif len(segs) >= 3:
                user, pwd = segs[0], segs[1]
            else:
                logging.error("URL remota no válida: %s", raw_url)
                continue

            logging.info("Creds extraídas de %s → dns=%s, user=%s", drive_file_id, dns, user)

            # ----- 4) Duplica local_updated a temp y procesa -----
            temp_path = os.path.join(
                UPLOAD_FOLDER,
                f"{playlist_id}_{drive_file_id}_to_upload.m3u"
            )
            shutil.copy(local_updated, temp_path)

            # Aquí tu función sustituye DNS/user/pwd en todas las URLs
            process_m3u_file(temp_path, dns, user, pwd)

            # ----- 5) Sube temp manteniendo el mismo fileId -----
            media = MediaFileUpload(
                temp_path,
                mimetype='application/octet-stream',
                resumable=False
            )
            updated = drive_service.files().update(
                fileId     = drive_file_id,
                media_body = media
            ).execute()

            logging.info(
                "Actualizado en Drive: playlist=%s fileId=%s",
                playlist_id, updated.get('id')
            )

            # (Opcional) borra el temp
            os.remove(temp_path)

        except Exception:
            logging.exception(
                "Error actualizando Drive fileId=%s para playlist=%s",
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
            "error": "File not found on server"
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
