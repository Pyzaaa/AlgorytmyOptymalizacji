import numpy as np
import json
import matplotlib.pyplot as plt
from collections import defaultdict
from optimization import create_g_c_mapping, parallel_fitness
import os
import re


def open_json(file_name):
    with open(file_name, 'r', encoding='utf-8') as file:
        return json.load(file)


def print_occupation(sol, g_c_mapping, r_s, t_s):
    """
        Wypisanie podsumowań w celu walidacji.
    """
    s1 = {
        g: int(np.any(sol, axis=(1, 2, 3))[idx].sum())
        for g, idx in g_c_mapping.items()
    }
    print("Zajętość grup studenckich:")
    print(json.dumps(s1, indent=2))

    s2 = {
        room: int(sol.sum(axis=(0, 1, 3))[idx])
        for idx, room in enumerate(r_s)
    }
    print("Zajętość pokoi:")
    print(json.dumps(s2, indent=2))

    s3 = {
        teacher: int(sol.sum(axis=(0, 2, 3))[idx])
        for idx, teacher in enumerate(t_s)
    }
    print("Zajętość prowadzących (top 10):")
    print(sorted(list(s3.items()), key=lambda x: x[1], reverse=True)[:10])
    print()


def print_teacher_schedule(sol, t_idx, c_s, t_s, r_s, ts_s):
    """
        Wypisuje listę przypisanych kursów dla danego nauczyciela.
    """
    c, _, r, ts = sol.shape
    print(f"Plan zajęć: {t_s[t_idx]}")
    for ts_idx in range(ts):
        for c_idx in range(c):
            for r_idx in range(r):
                if sol[c_idx, t_idx, r_idx, ts_idx]:
                    print(f"{ts_s[ts_idx]}, sala: {r_s[r_idx]} - {c_s[c_idx]}")
    print()


def print_student_group_schedule(sol, sg_code, c_s, t_s, r_s, ts_s, g_c_mapping):
    """
        Wypisuje listę przypisanych kursów dla danej grupy studenckiej.
    """
    c, t, r, ts = sol.shape
    print(f"Plan zajęć: {sg_code}")
    for ts_idx in range(ts):
        for r_idx in range(r):
            for t_idx in range(t):
                for c_idx in g_c_mapping[sg_code]:
                    if sol[c_idx, t_idx, r_idx, ts_idx]:
                        print(f"{ts_s[ts_idx]}, sala: {r_s[r_idx]} - {c_s[c_idx]} - {t_s[t_idx]}")
    print()


def find_top_rooms_and_print_schedules(ind, c_s, t_s, r_s, ts_s, top_n=10):
    """
        Wypisuje listę przypisanych kursów dla najwięcej zajętych sal.
    """
    c, t, r, ts = ind.shape
    assignment_counts = np.sum(ind, axis=(0, 1, 3))  # shape: (r,)

    top_rooms_indices = np.argsort(assignment_counts)[::-1][:top_n]

    print(f"Top {top_n} rooms with most assignments:\n")
    for idx, r_idx in enumerate(top_rooms_indices, 1):
        print(f"{idx}. Room: {r_s[r_idx]} - {assignment_counts[r_idx]} assignments\n")

        for ts_idx in range(ts):
            scheduled = []
            for c_idx in range(c):
                for t_idx in range(t):
                    if ind[c_idx, t_idx, r_idx, ts_idx]:
                        scheduled.append((ts_s[ts_idx], t_s[t_idx], c_s[c_idx]))
            for ts_val, teacher, course in scheduled:
                print(f"{ts_val}, Teacher: {teacher}, Course: {course}")
        print("-" * 40)


def print_timeslot_schedule(ind, ts_name, c_s, t_s, r_s, ts_s):
    """
        Wypisuje listę przypisanych kursów dla danego okna czasowego.
    """
    try:
        ts_idx = ts_s.index(ts_name)
    except ValueError:
        print(f"Time slot '{ts_name}' not found.")
        return

    c, t, r, ts = ind.shape
    print(f"\nSchedule for Time Slot: {ts_name}\n{'=' * 40}")
    found = False

    for c_idx in range(c):
        for t_idx in range(t):
            for r_idx in range(r):
                if ind[c_idx, t_idx, r_idx, ts_idx]:
                    print(f"Course: {c_s[c_idx]}\n  Teacher: {t_s[t_idx]}\n  Room: {r_s[r_idx]}\n")
                    found = True

    if not found:
        print("No assignments found at this time slot.")


def sanitize_filename(name):
    return name.replace("/", "_").replace("\\", "_").replace(":", "_").replace("*", "_")


def plot_schedule_from_data(s_data, label, image_path=None):
    """
        Tworzy wizualizację planu zajęć.
    """
    days = ["Pon", "Wto", "Śro", "Czw", "Pią"]
    hours = ["7:30", "9:15", "11:15", "13:15", "15:15", "17:05", "18:45"]
    timetable = defaultdict(lambda: [""] * len(hours))

    for entry in s_data:
        ts = entry["timeslot"]
        for day in days:
            if ts.startswith(day):
                hour = ts.split()[1]
                if hour in hours:
                    hour_idx = hours.index(hour)
                    line = f"{entry['course_id']}\n{entry['teacher']}\n{entry['room']}"
                    timetable[day][hour_idx] += line + "\n"

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_axis_off()

    table_data = []
    for i, hour in enumerate(hours):
        row = [hour]
        for day in days:
            cell = timetable[day][i].strip()
            row.append(cell)
        table_data.append(row)

    col_labels = ["Godzina"] + days
    table = ax.table(cellText=table_data, colLabels=col_labels, loc='center', cellLoc='left')
    table.scale(1, 2)
    table.auto_set_font_size(False)
    table.set_fontsize(8)

    plt.title(f"Plan dla: {label}", fontsize=14)
    plt.tight_layout()

    if image_path:
        plt.savefig(image_path, dpi=300)
        plt.close(fig)
        print(f"Plan zapisany do {image_path}")
    else:
        plt.show()


def get_group_schedule_data(ind, group_code, c_s, t_s, r_s, ts_s):
    c, t, r, ts = ind.shape
    schedule = []

    for ts_idx in range(ts):
        for c_idx in range(c):
            if group_code not in c_s[c_idx]:
                continue
            for t_idx in range(t):
                for r_idx in range(r):
                    if ind[c_idx, t_idx, r_idx, ts_idx]:
                        schedule.append({
                            "course_id": c_s[c_idx],
                            "teacher": t_s[t_idx],
                            "room": r_s[r_idx],
                            "timeslot": ts_s[ts_idx]
                        })
    return schedule


def get_room_schedule_data(ind, room_idx, c_s, t_s, r_s, ts_s):
    c, t, r, ts = ind.shape
    schedule = []

    for ts_idx in range(ts):
        for c_idx in range(c):
            for t_idx in range(t):
                if ind[c_idx, t_idx, room_idx, ts_idx]:
                    schedule.append({
                        "course_id": c_s[c_idx],
                        "teacher": t_s[t_idx],
                        "room": r_s[room_idx],
                        "timeslot": ts_s[ts_idx]
                    })
    return schedule


def get_teacher_schedule_data(ind, teacher_idx, c_s, t_s, r_s, ts_s):
    c, t, r, ts = ind.shape
    schedule = []

    for ts_idx in range(ts):
        for c_idx in range(c):
            for r_idx in range(r):
                if ind[c_idx, teacher_idx, r_idx, ts_idx]:
                    schedule.append({
                        "course_id": c_s[c_idx],
                        "teacher": t_s[teacher_idx],
                        "room": r_s[r_idx],
                        "timeslot": ts_s[ts_idx]
                    })
    return schedule


if __name__ == "__main__":

    course_data = open_json("Final_load_data/merged_filtered_course_data.json")
    rooms_type_mapping_data = open_json("Final_load_data/final_class_type_to_rooms.json")

    # Filtrowanie kursów w celu ograniczenia liczby kursów <-----------
    allowed_fields = ["ISA", "IST", "INS", "ITE"]
    course_data = {key: val for key, val in course_data.items() if val["field"] in allowed_fields}

    courses = sorted(course_data.keys())
    teachers = sorted(set(v for course in course_data.values() for v in course.get("lecturers", [])))
    rooms = sorted(set(v for l in rooms_type_mapping_data.values() for v in l))

    with open("teacher_preferences2.json") as f:
        teacher_preferences = json.load(f)

    time_slots = [
        "Pon 7:30", "Pon 9:15", "Pon 11:15", "Pon 13:15", "Pon 15:15", "Pon 17:05", "Pon 18:45",
        "Wto 7:30", "Wto 9:15", "Wto 11:15", "Wto 13:15", "Wto 15:15", "Wto 17:05", "Wto 18:45",
        "Śro 7:30", "Śro 9:15", "Śro 11:15", "Śro 13:15", "Śro 15:15", "Śro 17:05", "Śro 18:45",
        "Czw 7:30", "Czw 9:15", "Czw 11:15", "Czw 13:15", "Czw 15:15", "Czw 17:05", "Czw 18:45",
        "Pią 7:30", "Pią 9:15", "Pią 11:15", "Pią 13:15", "Pią 15:15", "Pią 17:05", "Pią 18:45",
    ]
    
    input_dir = "output_solver"

    best = np.load(f"{input_dir}/best.npz")['best']

    # extract one individual from original pop
    # best = np.load(f"{input_dir}/original_population.npz")['population'][...,0]

    groups_courses_mapping = create_g_c_mapping(course_data, courses)

    # print_occupation(best, groups_courses_mapping, rooms, teachers)

    # for t_idx in range(len(teachers)):
    #     print_teacher_schedule(best, t_idx, courses, teachers, rooms, time_slots)

    # for sg_code in groups_courses_mapping.keys():
    #     print_student_group_schedule(best, sg_code, courses, teachers, rooms, time_slots, groups_courses_mapping)

    # find_top_rooms_and_print_schedules(individual, courses, teachers, rooms, time_slots, top_n=10)

    # print_timeslot_schedule(individual, "Pon 7:30", courses, teachers, rooms, time_slots)

    # g_name = "IST-SI"
    # schedule_data = get_group_schedule_data(best, g_name, courses, teachers, rooms, time_slots)
    # plot_schedule_from_data(schedule_data, g_name)

    # t_name = "Wojciech Thomas"
    # t_idx = teachers.index(t_name)
    # teacher_schedule = get_teacher_schedule_data(best, t_idx, courses, teachers, rooms, time_slots)
    # plot_schedule_from_data(teacher_schedule, t_name)

    # r_name = "022"
    # r_idx = rooms.index(r_name)
    # room_schedule = get_room_schedule_data(best, r_idx, courses, teachers, rooms, time_slots)
    # plot_schedule_from_data(room_schedule, f"Sala {r_name}")

    # Extract unique group names from course codes
    group_names = set()
    for course in courses:
        match = re.match(r"W\d{2}([A-Z\-]+)", course)
        if match:
            group_names.add(match.group(1))

    # output_dir = "schedules/groups"
    # os.makedirs(output_dir, exist_ok=True)
    # for g_name in group_names:
    #     schedule_data = get_group_schedule_data(best, g_name, courses, teachers, rooms, time_slots)
    #     plot_schedule_from_data(schedule_data, g_name, image_path=f"{output_dir}/{g_name}.png")

    output_dir = "schedules/teachers"
    os.makedirs(output_dir, exist_ok=True)
    for name in teachers:
        t_idx = teachers.index(name)
        teacher_schedule = get_teacher_schedule_data(best, t_idx, courses, teachers, rooms, time_slots)
        plot_schedule_from_data(teacher_schedule, name, image_path=f"{output_dir}/{name}.png")

    # output_dir = "schedules/rooms"
    # os.makedirs(output_dir, exist_ok=True)
    # for name in rooms:
    #     t_idx = rooms.index(name)
    #     room_schedule = get_room_schedule_data(best, t_idx, courses, teachers, rooms, time_slots)
    #     safe_name = sanitize_filename(name)
    #     plot_schedule_from_data(room_schedule, name, image_path=f"{output_dir}/{safe_name}.png")
