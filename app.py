import requests
import csv
import re

# URL
CSV_URL = "https://docs.google.com/spreadsheets/d/1JZ3K-7VKtXdZfnqcUBU2Mv2cGKwgWa73NACNQFrylD4/gviz/tq?tqx=out:csv"

# Request the file
response = requests.get(CSV_URL)
response.encoding = 'utf-8'

# Verify it is valid
if response.text.startswith("function"):
    print("❌ Error: The URL does not return a valid CSV or it is a private file.")
    exit()

# Leer los datos del CSV
data = list(csv.reader(response.text.splitlines()))

# Mostrar opciones al usuario
print("\nID | Service | Countries | Main Category | M3U File Link")
print("-" * 90)

for row in data[1:]:  # Saltar encabezados
    print(f"{row[0]:<5} | {row[1]:<20} | {row[2]:<15} | {row[3]:<20}")

# Ask for ID
user_choice = input("\nEnter the ID of the service you want to download: ").strip()

# Search for selected ID
selected_row = None
for row in data[1:]:
    if row[0] == user_choice:
        selected_row = row
        break

if not selected_row:
    print("❌ Invalid ID selected.")
    exit()

# Obtaining URL
m3u_url = selected_row[4]
print(f"\n🔗 Selected M3U URL: {m3u_url}")

# Extract ID from URL
match = re.search(r"[-\w]{25,}", m3u_url)
if not match:
    print("❌ Error: Could not extract the file ID from the Google Drive URL.")
    exit()

file_id = match.group(0)

# Create URL to download with ID
download_url = f"https://drive.google.com/uc?id={file_id}&export=download"
print(f"⬇️ Downloading from: {download_url}")

# Download file
file_response = requests.get(download_url)

# Save file
original_filename = "original_playlist.m3u"
with open(original_filename, "wb") as file:
    file.write(file_response.content)

print(f"✅ File downloaded as: {original_filename}")

# Ask for DNS, Username and Password
dns = input("\nEnter the DNS: ").strip()
username = input("Enter the Username: ").strip()
password = input("Enter the Password: ").strip()

# Read file
with open(original_filename, "r", encoding="utf-8") as file:
    file_content = file.read()
    
#Replace data
file_content = file_content.replace("DNS", dns)
file_content = file_content.replace("USERNAME", username)
file_content = file_content.replace("PASSWORD", password)

# Save file modified
modified_filename = "modified_playlist.m3u"
with open(modified_filename, "w", encoding="utf-8") as file:
    file.write(file_content)

print(f"✅ Modified file saved as: {modified_filename}")
