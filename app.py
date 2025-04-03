import csv
import requests

# Descargar el Google Sheet como CSV (Reemplaza 'YOUR_CSV_URL' con el enlace real)
CSV_URL = "YOUR_CSV_URL"
response = requests.get(CSV_URL)
csv_content = response.text

# Guardar CSV localmente
csv_filename = "data.csv"
with open(csv_filename, "w", encoding="utf-8") as file:
    file.write(csv_content)

# Leer el archivo CSV
data = []
with open(csv_filename, newline="", encoding="utf-8") as file:
    reader = csv.reader(file)
    headers = next(reader)  # Obtener encabezados
    for row in reader:
        data.append(row)

# Mostrar las primeras 4 columnas de cada fila
print("ID | Service | Countries | Main Category")
for row in data:
    print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]}")

# Pedir al usuario que seleccione un ID
selected_id = input("\nEnter the ID of the row you want to use: ")
selected_row = next((row for row in data if row[0] == selected_id), None)

if selected_row:
    # Pedir credenciales
    dns = input("Enter DNS: ")
    username = input("Enter Username: ")
    password = input("Enter Password: ")

    # Descargar archivo M3U de la URL en la 5ª columna
    m3u_url = selected_row[4]
    m3u_response = requests.get(m3u_url)
    m3u_content = m3u_response.text

    # Reemplazar placeholders
    m3u_content = m3u_content.replace("DNS", dns).replace("USERNAME", username).replace("PASSWORD", password)

    # Guardar el archivo modificado
    with open("modified_playlist.m3u", "w", encoding="utf-8") as file:
        file.write(m3u_content)

    print("\nM3U file has been successfully modified and saved as 'modified_playlist.m3u'!")
else:
    print("ID not found.")
