import requests
import json

# API endpoint and parameters
url = "https://apps.usos.pwr.edu.pl/services/geo/building2"
params = {
    "building_id": "C-2",
    "fields": "id|name|rooms"
}

# Send request
response = requests.get(url, params=params)

# Proceed only if the request was successful
if response.status_code == 200:
    data = response.json()

    # Filter the response
    filtered_data = {
        "id": data.get("id"),
        "name": data.get("name"),
        "rooms": [{"id": room["id"], "number": room["number"]} for room in data.get("rooms", [])]
    }

    # Save filtered output to a JSON file
    with open("building_roomsC2.json", "w", encoding="utf-8") as f:
        json.dump(filtered_data, f, ensure_ascii=False, indent=4)

    print("Filtered data saved to 'building_roomsC1.json'")
else:
    print(f"Request failed with status code {response.status_code}")
