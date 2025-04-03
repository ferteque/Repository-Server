import csv
import requests
from io import StringIO

# Descargar el Google Sheet como CSV (Reemplaza 'YOUR_CSV_URL' con el enlace real)
CSV_URL = "YOUR_CSV_URL"
response = requests.get(CSV_URL)

if response.status_code == 200:
    csv_content = response.text

    # Leer los datos como un archivo CSV
    data = []
    reader = csv.reader(StringIO(csv_content))
    
    # Saltar la primera y segunda fila
    next(reader, None)  # Salta fila 1 (mensaje)
    next(reader, None)  # Salta fila 2 (encabezados)

    # Leer filas restantes
    for row in reader:
        if len(row) >= 5:  # Asegurar que tenga al menos 5 columnas
            data.append(row)

    # Mostrar las primeras 4 columnas de cada fila
    # Mostrar las primeras 4 columnas de cada fila de forma legible
    print("\nID | Service | Countries | Main Category")
    print("-" * 50)  # Línea separadora

    for row in data:
        print(f"{row[0]:<5} | {row[1]:<20} | {row[2]:<15} | {row[3]:<20}")

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
        if m3u_url.startswith("http"):  # Asegurar que es un enlace válido
            m3u_response = requests.get(m3u_url)
            if m3u_response.status_code == 200:
                m3u_content = m3u_response.text

                # Reemplazar placeholders
                m3u_content = m3u_content.replace("DNS", dns).replace("USERNAME", username).replace("PASSWORD", password)

                # Guardar el archivo modificado
                with open("modified_playlist.m3u", "w", encoding="utf-8") as file:
                    file.write(m3u_content)

                print("\n✅ M3U file successfully modified and saved as 'modified_playlist.m3u'!")
            else:
                print("\n❌ Failed to download M3U file.")
        else:
            print("\n❌ Invalid M3U URL.")
    else:
        print("\n❌ ID not found.")

else:
    print("\n❌ Failed to download the CSV file.")
