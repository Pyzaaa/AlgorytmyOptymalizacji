import json
import random

# === ŚCIEŻKI DO PLIKÓW ===
COURSE_FILE = "final json/course_field_type_name_mapping.json"
LECTURER_FILE = "final json/course_lecturer_mapping.json"

with open(COURSE_FILE, encoding="utf-8") as f:
    course_data = json.load(f)

with open(LECTURER_FILE, encoding="utf-8") as f:
    lecturer_data = json.load(f)

expanded_courses = {}
expanded_lecturers = dict(lecturer_data)

# === KONFIGURACJA ===

# Typy zajęć i ich szanse (waga)
class_type_distribution = {
    "W": ("wykład", 0.6),
    "L": ("laboratorium", 0.5),
    "C": ("ćwiczenia", 0.5),
    "S": ("seminarium", 0.2),
    "P": ("projekt", 0.3)
}

# Czy grupy mogą mieć więcej niż jeden typ zajęć?
ALLOW_MULTIPLE_TYPES = True

# Ilość typów maksymalnie przypisanych do jednego kursu (jeśli dozwolone)
MAX_TYPES_PER_COURSE = 2


def get_random_class_types():
    """Randomly select one or more class types based on defined weights."""
    suffixes = list(class_type_distribution.keys())
    weights = [class_type_distribution[suffix][1] for suffix in suffixes]

    selected_suffixes = random.choices(
        population=suffixes,
        weights=weights,
        k = random.choices([1, 2], weights=[0.3, 0.7])[0]  # 70% chance of 1, 30% chance of 2

    )
    return list(set(selected_suffixes))  # remove duplicates


for code, info in course_data.items():
    if code.endswith("G"):
        base = code[:-1]
        selected_suffixes = get_random_class_types()
        for suffix in selected_suffixes:
            new_code = base + suffix
            class_type_label = class_type_distribution[suffix][0]
            expanded_courses[new_code] = {
                "course_name": info["course_name"],
                "field": info["field"],
                "degree": info["degree"],
                "class_type": class_type_label
            }
            if code in lecturer_data:
                expanded_lecturers[new_code] = lecturer_data[code]
    else:
        expanded_courses[code] = info  # keep original if not ending in G

# === ZAPISYWANIE ===

with open("final json/final_course_data.json", "w", encoding="utf-8") as f:
    json.dump(expanded_courses, f, ensure_ascii=False, indent=4)

with open("final json/final_course_lecturers.json", "w", encoding="utf-8") as f:
    json.dump(expanded_lecturers, f, ensure_ascii=False, indent=4)

print("Pliki zapisane: final_course_data.json, final_course_lecturers.json")
