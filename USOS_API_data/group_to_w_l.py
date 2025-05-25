import json

# === ŚCIEŻKI DO PLIKÓW ===
COURSE_FILE = "USOS_API_data/final json/course_field_type_name_mapping.json"
LECTURER_FILE = "USOS_API_data/final json/course_lecturer_mapping.json"

with open(COURSE_FILE, encoding="utf-8") as f:
    course_data = json.load(f)

with open(LECTURER_FILE, encoding="utf-8") as f:
    lecturer_data = json.load(f)

expanded_courses = {}
expanded_lecturers = dict(lecturer_data)  

for code, info in course_data.items():
    if code.endswith("G"):
        base = code[:-1]
        for suffix, class_type in {"W": "wykład", "L": "laboratorium"}.items():
            new_code = base + suffix
            expanded_courses[new_code] = {
                "course_name": info["course_name"],
                "field": info["field"],
                "degree": info["degree"],
                "class_type": class_type
            }
            if code in lecturer_data:
                expanded_lecturers[new_code] = lecturer_data[code]
    else:
        expanded_courses[code] = info 

with open("USOS_API_data/final json/final_course_data.json", "w", encoding="utf-8") as f:
    json.dump(expanded_courses, f, ensure_ascii=False, indent=4)

with open("USOS_API_data/final json/final_course_lecturers.json", "w", encoding="utf-8") as f:
    json.dump(expanded_lecturers, f, ensure_ascii=False, indent=4)

print("Pliki zapisane: final_course_data.json, final_course_lecturers.json")
