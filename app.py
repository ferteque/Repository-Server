from flask import Flask, request, send_file, render_template
import requests
import re
import io
from flask_cors import CORS


app = Flask(__name__)

CORS(app, resources={r"/process": {"origins": ["https://repository-server.onrender.com" , "https://striking-orella-ferteque-e35fe763.koyeb.app"]}})

@app.route('/')
def home():
    return render_template("index.html") 

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    id_selected = data['id']
    dns = data['dns']
    username = data['username']
    password = data['password']
    m3u_url = data['m3uUrl']

    if "drive.google.com" in m3u_url:
        match = re.search(r"[-\w]{25,}", m3u_url)
        if not match:
            return "Error: Could not extract the file ID from the URL.", 400
        file_id = match.group(0)
        download_url = f"https://drive.google.com/uc?id={file_id}&export=download"

    elif "github.com" in m3u_url or "raw.githubusercontent.com" in m3u_url:
        download_url = m3u_url
    else:
        return "Error: Unsupported URL. Only Google Drive and GitHub links are supported.", 400

    try:
        response = requests.get(download_url, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f"Download error: {str(e)}", 500

    content = response.content.decode('utf-8')

    content = re.sub(r'(?<!http://)(DNS)', r'http://\1', content)
    content = re.sub(r'(?<!http://)(dns)', r'http://\1', content)
    
    content = content.replace("DNS", dns).replace("dns", dns)
    content = content.replace("USERNAME", username).replace("username", username)
    content = content.replace("PASSWORD", password).replace("password", password)

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
