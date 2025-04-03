import requests
import csv
import re

# URL del Google Sheet en formato CSV
CSV_URL = "https://docs.google.com/spreadsheets/d/ID_DEL_DOCUMENTO/gviz/tq?tqx=out:csv"

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

for row in data[2:]:  # Saltar encabezados
    print(f"{row[0]:<5} | {row[1]:<20} | {row[2]:<15} | {row[3]:<20} | {row[4]}")

# Pedir al usuario que elija un ID
user_choice = input("\nEnter the ID of the service you want to download: ").strip()

# Buscar la fila con ese ID
selected_row = None
for row in data[2:]:
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

# Guardar el archivo en local
output_filename = "downloaded_playlist.m3u"
with open(output_filename, "wb") as file:
    file.write(file_response.content)

print(f"✅ File saved as: {output_filename}")
