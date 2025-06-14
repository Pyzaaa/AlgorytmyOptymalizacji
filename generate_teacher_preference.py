import random
import json
from optimization import *



def generate_sparse_teacher_preferences(
        teachers,
        time_slots,
        teachers_with_prefs=None,
        output_path="teacher_preferences.json",
):
    """
    Generate consistent sparse preferences for selected teachers only.

    teachers_with_prefs: list of teacher indexes to assign preferences to (others get no prefs).
    time_slots: list of all time slot strings (e.g. "Pon 7:30").
    """

    if teachers_with_prefs is None:
        odds = 1
        num_pref_teachers = max(1, int(len(teachers) * odds))
        teachers_with_prefs = random.sample(range(len(teachers)), num_pref_teachers)

    # Define some consistent preference patterns (dislike=1, like=5)
    # Patterns are dict {slot_index: score}
    patterns = []

    # Map days to their slot indexes (assuming 5 days, equal time slots per day)
    time_slots_per_day = len(time_slots) // 5
    days = ["Pon", "Wto", "Śro", "Czw", "Pią"]

    # Helper: find slot indexes containing day substring
    def slots_for_day(day_name):
        return [i for i, ts in enumerate(time_slots) if ts.startswith(day_name)]

    # Pattern 1: Dislike entire Monday
    monday_slots = slots_for_day("Pon")
    patterns.append({str(i): 1 for i in monday_slots})

    # Pattern 1-1: Dislike entire Friday
    friday_slots = slots_for_day("Pią")
    patterns.append({str(i): 1 for i in friday_slots})

    # Pattern 2: Dislike all morning slots (first 3 slots per day)
    morning_slots = []
    for d in range(5):
        start = d * time_slots_per_day
        morning_slots.extend(range(start, start + 3))
    patterns.append({str(i): 1 for i in morning_slots})

    # Pattern 3: Dislike all afternoons (slots 3-5 per day)
    afternoon_slots = []
    for d in range(5):
        start = d * time_slots_per_day
        afternoon_slots.extend(range(start + 3, start + 6))
    patterns.append({str(i): 1 for i in afternoon_slots})

    # Pattern 4: Dislike late evening slots (last 2 slots each day)
    evening_slots = []
    for d in range(5):
        start = d * time_slots_per_day
        evening_slots.extend(range(start + time_slots_per_day - 2, start + time_slots_per_day))
    patterns.append({str(i): 1 for i in evening_slots})

    # Pattern 5: Dislike mid-day slots (slots 2-4 per day)
    midday_slots = []
    for d in range(5):
        start = d * time_slots_per_day
        midday_slots.extend(range(start + 2, start + 5))
    patterns.append({str(i): 1 for i in midday_slots})

    preferences = {}

    for t_idx in range(len(teachers)):
        if t_idx in teachers_with_prefs:
            # Assign a random pattern to this teacher
            pattern = random.choice(patterns)
            preferences[str(t_idx)] = pattern
        else:
            # No preferences for this teacher
            preferences[str(t_idx)] = {}

    with open(output_path, "w") as f:
        json.dump(preferences, f, indent=2)

    print(f"Consistent sparse preferences saved to {output_path}")


def print_teacher_preferences(preferences_path, teachers, time_slots):
    """
    preferences_path: path to sparse JSON preference file (indexed teachers and time slots)
    teachers: list of teacher names by index
    time_slots: list of time slot names by index
    """
    with open(preferences_path, "r") as f:
        prefs = json.load(f)

    for t_idx_str, slot_prefs in prefs.items():
        t_idx = int(t_idx_str)
        teacher_name = teachers[t_idx] if t_idx < len(teachers) else f"Unknown-{t_idx}"

        print(f"Teacher: {teacher_name} (index {t_idx})")
        for ts_idx_str, score in sorted(slot_prefs.items(), key=lambda x: int(x[0])):
            ts_idx = int(ts_idx_str)
            time_slot_name = time_slots[ts_idx] if ts_idx < len(time_slots) else f"Unknown-{ts_idx}"
            sentiment = "likes" if int(score) >= 4 else ("dislikes" if int(score) <= 2 else "neutral")

            print(f"  Time slot: {time_slot_name} (index {ts_idx}) - Preference: {score} ({sentiment})")
        print()


if __name__ == "__main__":
    course_data = open_json("Final_load_data/merged_filtered_course_data.json")
    rooms_type_mapping_data = open_json("Final_load_data/final_class_type_to_rooms.json")

    courses = sorted(course_data.keys())
    teachers = sorted(set(v for course in course_data.values() for v in course.get("lecturers", [])))
    rooms = sorted(set(v for l in rooms_type_mapping_data.values() for v in l))
    time_slots = [
        "Pon 7:30", "Pon 9:15", "Pon 11:15", "Pon 13:15", "Pon 15:15", "Pon 17:05", "Pon 18:45",
        "Wto 7:30", "Wto 9:15", "Wto 11:15", "Wto 13:15", "Wto 15:15", "Wto 17:05", "Wto 18:45",
        "Śro 7:30", "Śro 9:15", "Śro 11:15", "Śro 13:15", "Śro 15:15", "Śro 17:05", "Śro 18:45",
        "Czw 7:30", "Czw 9:15", "Czw 11:15", "Czw 13:15", "Czw 15:15", "Czw 17:05", "Czw 18:45",
        "Pią 7:30", "Pią 9:15", "Pią 11:15", "Pią 13:15", "Pią 15:15", "Pią 17:05", "Pią 18:45",
    ]

    course_teacher_mapping = create_c_t_mapping(course_data, courses, teachers)
    courses_rooms_mapping = create_c_r_mapping(rooms_type_mapping_data, course_data, rooms, courses)
    groups_courses_mapping = create_g_c_mapping(course_data, courses)
    # Call this once to create preferences
    preferences_path = "teacher_preferences100.json"


    generate_sparse_teacher_preferences(teachers, time_slots, output_path=preferences_path)

    print_teacher_preferences(preferences_path, teachers, time_slots)