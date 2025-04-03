import requests
import csv
import re

# URL del Google Sheet en formato CSV
CSV_URL = "https://docs.google.com/spreadsheets/d/1JZ3K-7VKtXdZfnqcUBU2Mv2cGKwgWa73NACNQFrylD4/gviz/tq?tqx=out:csv"

# Obtener el contenido del Google Sheet
response = requests.get(CSV_URL)
response.encoding = 'utf-8'

# Verificar que la respuesta no sea código JavaScript
if response.text.startswith("function"):
    print("❌ Error: La URL no devuelve un CSV. Verifica los permisos del archivo.")
    exit()

# Leer los datos del CSV
data = list(csv.reader(response.text.splitlines()))

# Mostrar opciones al usuario
print("\nID | Service | Countries | Main Category | M3U File Link")
print("-" * 90)

for row in data[1:]:  # Saltar encabezados
    print(f"{row[0]:<5} | {row[1]:<20} | {row[2]:<15} | {row[3]:<20}")

# Pedir al usuario que elija un ID
user_choice = input("\nEnter the ID of the service you want to download: ").strip()

# Buscar la fila con ese ID
selected_row = None
for row in data[1:]:
    if row[0] == user_choice:
        selected_row = row
        break

if not selected_row:
    print("❌ Invalid ID selected.")
    exit()

# Obtener la URL del archivo M3U
m3u_url = selected_row[4]
print(f"\n🔗 Selected M3U URL: {m3u_url}")

# Extraer el ID del archivo de Google Drive
match = re.search(r"[-\w]{25,}", m3u_url)
if not match:
    print("❌ Error: Could not extract the file ID from the Google Drive URL.")
    exit()

file_id = match.group(0)

# Construir la URL de descarga directa de Google Drive
download_url = f"https://drive.google.com/uc?id={file_id}&export=download"
print(f"⬇️ Downloading from: {download_url}")

# Descargar el archivo M3U
file_response = requests.get(download_url)

# Guardar el archivo original
original_filename = "original_playlist.m3u"
with open(original_filename, "wb") as file:
    file.write(file_response.content)

print(f"✅ File downloaded as: {original_filename}")

# Pedir al usuario DNS, Username y Password
dns = input("\nEnter the DNS: ").strip()
username = input("Enter the Username: ").strip()
password = input("Enter the Password: ").strip()

# Leer el archivo y reemplazar los valores
with open(original_filename, "r", encoding="utf-8") as file:
    file_content = file.read()

file_content = file_content.replace("DNS", dns)
file_content = file_content.replace("USERNAME", username)
file_content = file_content.replace("PASSWORD", password)

# Guardar el archivo modificado
modified_filename = "modified_playlist.m3u"
with open(modified_filename, "w", encoding="utf-8") as file:
    file.write(file_content)

print(f"✅ Modified file saved as: {modified_filename}")
