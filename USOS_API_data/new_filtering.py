import json
import re

FINAL_DATA_PATH = "USOS_API_data/final json/FINAL_all_data_combined.json"
ROOM_DETAILS_PATH = "USOS_API_data/room_details-att.json"
COURSE_EDITIONS_PATH = "USOS_API_data/course_editions_with_lecturers_sorted.json"

with open(FINAL_DATA_PATH, encoding="utf-8") as f:
    final_data = json.load(f)

with open(ROOM_DETAILS_PATH, encoding="utf-8") as f:
    room_details = json.load(f)

with open(COURSE_EDITIONS_PATH, encoding="utf-8") as f:
    course_editions = json.load(f)

course_codes = final_data["courses"]
suffix_to_type = {
    "S": "seminarium",
    "C": "ćwiczenia",
    "L": "laboratorium",
    "W": "wykład",
    "D": "praca dyplomowa",
    "P": "projekt",
    "G": "grupa"
}

course_to_data = {}

for code in course_codes:
    match = re.match(r"W04([A-Z]+)-([A-Z]{2})\d{4}[A-Z]$", code)
    if match:
        kierunek = match.group(1)
        stopien = match.group(2)
    else:
        kierunek = "Unknown"
        stopien = "Unknown"

    class_type = suffix_to_type.get(code[-1], "nieznany")

    course_name = "Unknown"
    for k, v in course_editions.items():
        if v.get("course_id") == code:
            course_name = v.get("course_name", {}).get("pl", "Unknown")
            break

    course_to_data[code] = {
        "course_name": course_name,
        "field": kierunek,
        "degree": stopien,
        "class_type": class_type
    }


valid_room_types = {"LAB_KOMP", "LAB_SPEC", "SALA_SEM", "SALA_CW", "SALA_WYK_MALA"}
class_type_to_rooms = {}

for room in room_details:
    if room["type"] == "didactics_room":
        for attr in room.get("attributes", []):
            attr_id = attr.get("id")
            if attr_id in valid_room_types:
                class_type_to_rooms.setdefault(attr_id, []).append(room["number"])

with open("USOS_API_data/final json/course_direction_type_name_mapping.json", "w", encoding="utf-8") as f:
    json.dump(course_to_data, f, ensure_ascii=False, indent=4)

with open("USOS_API_data/final json/class_type_to_rooms.json", "w", encoding="utf-8") as f:
    json.dump(class_type_to_rooms, f, ensure_ascii=False, indent=4)

print("Pliki zapisane: course_direction_type_name_mapping.json, class_type_to_rooms.json")
