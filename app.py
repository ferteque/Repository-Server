from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    id_selected = data['id']
    dns = data['dns']
    username = data['username']
    password = data['password']
    m3u_url = data['m3uUrl']

    # Extraer el ID del archivo de Google Drive
    match = re.search(r"[-\w]{25,}", m3u_url)
    if not match:
        return "Error: Could not extract the file ID from the URL.", 400

    file_id = match.group(0)
    download_url = f"https://drive.google.com/uc?id={file_id}&export=download"

    # Descargar el archivo M3U
    file_response = requests.get(download_url)
    original_filename = "original_playlist.m3u"
    with open(original_filename, "wb") as file:
        file.write(file_response.content)

    # Leer y modificar el archivo
    with open(original_filename, "r", encoding="utf-8") as file:
        file_content = file.read()

    file_content = file_content.replace("DNS", dns)
    file_content = file_content.replace("USERNAME", username)
    file_content = file_content.replace("PASSWORD", password)

    # Guardar el archivo final
    modified_filename = f"modified_playlist_{id_selected}.m3u"
    with open(modified_filename, "w", encoding="utf-8") as file:
        file.write(file_content)

    return send_file(modified_filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
