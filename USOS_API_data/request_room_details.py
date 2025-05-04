import requests
import json
import time  # optional: to avoid hammering the API

# Load the previously saved JSON with room IDs
with open("building_roomsC4.json", "r", encoding="utf-8") as f:
    building_data = json.load(f)

rooms = building_data.get("rooms", [])

# Prepare to collect room details
room_details = []

# API endpoint
url = "https://apps.usos.pwr.edu.pl/services/geo/room"
fields = "id|number|type|capacity|attributes"

# Loop through all room IDs and fetch data
for room in rooms:
    room_id = room["id"]
    params = {
        "room_id": room_id,
        "fields": fields
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        room_data = response.json()
        room_details.append(room_data)
    else:
        print(f"Failed to fetch data for room ID {room_id} (status {response.status_code})")

    time.sleep(0.2)  # polite delay to avoid overwhelming the server

# Save all room details to a new JSON file
with open("room_details-att-C4.json", "w", encoding="utf-8") as f:
    json.dump(room_details, f, ensure_ascii=False, indent=4)

print("Room details saved")
