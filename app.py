from flask import Flask, request, jsonify, send_file, render_template
import requests
import re
from flask_cors import CORS

const API_TOKEN = process.env.BIT_TOKEN

app = Flask(__name__)

CORS(app, resources={r"/process": {"origins": "https://repository-server.onrender.com"}})

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

    
    match = re.search(r"[-\w]{25,}", m3u_url)
    if not match:
        return "Error: Could not extract the file ID from the URL.", 400

    file_id = match.group(0)
    download_url = f"https://drive.google.com/uc?id={file_id}&export=download"

    
    file_response = requests.get(download_url)
    original_filename = "original_playlist.m3u"
    with open(original_filename, "wb") as file:
        file.write(file_response.content)

   
    with open(original_filename, "r", encoding="utf-8") as file:
        file_content = file.read()

    file_content = file_content.replace("DNS", dns)
    file_content = file_content.replace("USERNAME", username)
    file_content = file_content.replace("PASSWORD", password)

    file_content = file_content.replace("dns", dns)
    file_content = file_content.replace("username", username)
    file_content = file_content.replace("password", password)

    modified_filename = f"modified_playlist_{id_selected}.m3u"
    with open(modified_filename, "w", encoding="utf-8") as file:
        file.write(file_content)

    return send_file(modified_filename, as_attachment=True)

@app.route('/shorten', methods=['GET'])
    def shorten_url():
        long_url = request.args.get('url') 

        if not long_url:
            return jsonify({"error": "Bad URL"}), 400

        
        bitly_api_url = 'https://api-ssl.bitly.com/v4/shorten'
        headers = {
            'Authorization': f'Bearer {API_TOKEN}',
            'Content-Type': 'application/json'
        }
        data = {
            'long_url': long_url
        }

        response = requests.post(bitly_api_url, json=data, headers=headers)

        # Verificar la respuesta de la API
        if response.status_code == 200:
            short_url = response.json().get('link')  
            return jsonify({'shortUrl': short_url})
        else:
            return jsonify({'error': 'Error al acortar la URL', 'details': response.json()}), response.status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
