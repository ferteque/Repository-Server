from flask import Flask, render_template, request, send_file
import pandas as pd
import requests
import tempfile
import os
import json

app = Flask(__name__)

# Archivo donde se guarda el contador
COUNTER_FILE = "downloads.json"

# Cargar contador desde archivo
def load_counter():
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "r") as f:
            return json.load(f).get("downloads", 0)
    return 0

# Guardar contador en archivo
def save_counter(count):
    with open(COUNTER_FILE, "w") as f:
        json.dump({"downloads": count}, f)

download_count = load_counter()

@app.route("/process", methods=["POST"])
def process():
    global download_count
    download_count += 1
    save_counter(download_count)  # Guardar el contador actualizado

    # Obtener y modificar el archivo M3U
    selected_id = int(request.form["id"])
    dns = request.form["dns"]
    username = request.form["username"]
    password = request.form["password"]
    
    df = pd.read_csv("https://docs.google.com/spreadsheets/d/TU_SHEET_ID/gviz/tq?tqx=out:csv")
    row = df[df["ID"] == selected_id].iloc[0]
    m3u_url = row["M3U file Link"]
    
    response = requests.get(m3u_url)
    m3u_content = response.text
    m3u_content = m3u_content.replace("DNS", dns).replace("USERNAME", username).replace("PASSWORD", password)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".m3u", mode="w", encoding="utf-8")
    temp_file.write(m3u_content)
    temp_file.close()

    return send_file(temp_file.name, as_attachment=True, download_name="custom_playlist.m3u")

@app.route("/stats")
def stats():
    """Muestra el número de descargas."""
    return f"Total Downloads: {download_count}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
