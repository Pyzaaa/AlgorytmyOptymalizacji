import numpy as np
import json


def open_json(file_name):
    with open(file_name, 'r', encoding='utf-8') as file:
        return json.load(file)





def find_top_teachers_and_print_schedules(individual, c_s, t_s, r_s, ts_s, top_n=10):
    c, t, r, ts = individual.shape
    assignment_counts = np.sum(individual, axis=(0, 2, 3))  # shape: (t,)

    top_teachers_indices = np.argsort(assignment_counts)[::-1][:top_n]

    print(f"Top {top_n} teachers with most assignments:\n")
    for idx, t_idx in enumerate(top_teachers_indices, 1):
        print(f"{idx}. Teacher: {t_s[t_idx]} - {assignment_counts[t_idx]} assignments\n")

        for ts_idx in range(ts):
            scheduled = []
            for c_idx in range(c):
                for r_idx in range(r):
                    if individual[c_idx, t_idx, r_idx, ts_idx]:
                        scheduled.append((ts_s[ts_idx], c_s[c_idx], r_s[r_idx]))
            for ts_val, course, room in scheduled:
                print(f"{ts_val}, Course: {course}, Room: {room}")
        print("-" * 40)

def find_top_rooms_and_print_schedules(individual, c_s, t_s, r_s, ts_s, top_n=10):
    c, t, r, ts = individual.shape
    assignment_counts = np.sum(individual, axis=(0, 1, 3))  # shape: (r,)

    top_rooms_indices = np.argsort(assignment_counts)[::-1][:top_n]

    print(f"Top {top_n} rooms with most assignments:\n")
    for idx, r_idx in enumerate(top_rooms_indices, 1):
        print(f"{idx}. Room: {r_s[r_idx]} - {assignment_counts[r_idx]} assignments\n")

        for ts_idx in range(ts):
            scheduled = []
            for c_idx in range(c):
                for t_idx in range(t):
                    if individual[c_idx, t_idx, r_idx, ts_idx]:
                        scheduled.append((ts_s[ts_idx], t_s[t_idx], c_s[c_idx]))
            for ts_val, teacher, course in scheduled:
                print(f"{ts_val}, Teacher: {teacher}, Course: {course}")
        print("-" * 40)


def print_timeslot_schedule(individual, ts_name, c_s, t_s, r_s, ts_s):
    """
    Print schedule information for a specific time slot.

    Parameters:
        individual (ndarray): Shape (courses, teachers, rooms, timeslots)
        ts_name (str): Time slot label, e.g., "Pon 7:30"
        c_s (list): Course names
        t_s (list): Teacher names
        r_s (list): Room names
        ts_s (list): Time slot names
    """
    try:
        ts_idx = ts_s.index(ts_name)
    except ValueError:
        print(f"Time slot '{ts_name}' not found.")
        return

    c, t, r, ts = individual.shape
    print(f"\nSchedule for Time Slot: {ts_name}\n{'=' * 40}")
    found = False

    for c_idx in range(c):
        for t_idx in range(t):
            for r_idx in range(r):
                if individual[c_idx, t_idx, r_idx, ts_idx]:
                    print(f"Course: {c_s[c_idx]}\n  Teacher: {t_s[t_idx]}\n  Room: {r_s[r_idx]}\n")
                    found = True

    if not found:
        print("No assignments found at this time slot.")


def print_group_schedule(individual, group_code, c_s, t_s, r_s, ts_s):
    """
    Print schedule for a specific group (based on substring in course ID).

    Parameters:
        individual (ndarray): Shape (courses, teachers, rooms, timeslots)
        group_code (str): Substring to match in course ID (e.g., "IST-SI")
        c_s (list): Course names
        t_s (list): Teacher names
        r_s (list): Room names
        ts_s (list): Time slot names
    """
    c, t, r, ts = individual.shape
    print(f"\nSchedule for Group: {group_code}\n{'=' * 40}")
    found = False

    for ts_idx in range(ts):
        for c_idx in range(c):
            if group_code not in c_s[c_idx]:
                continue
            for t_idx in range(t):
                for r_idx in range(r):
                    if individual[c_idx, t_idx, r_idx, ts_idx]:
                        print(
                            f"Time: {ts_s[ts_idx]}\n  Course: {c_s[c_idx]}\n  Teacher: {t_s[t_idx]}\n  Room: {r_s[r_idx]}\n"
                        )
                        found = True

    if not found:
        print("No classes found for this group.")

import matplotlib.pyplot as plt
from collections import defaultdict

def plot_schedule_from_data(schedule_data, label, label_type="Group", image_path=None):
    """
    Plots a weekly timetable based on unified schedule data.

    Parameters:
        schedule_data (list): List of dicts with keys: course_id, teacher, room, timeslot
        label (str): Identifier for the entity (group name, teacher name, or room ID)
        label_type (str): One of "Group", "Teacher", or "Room" — used for plot title
        image_path (str or None): If provided, saves image to this path
    """
    # Define timetable structure
    days = ["Pon", "Wto", "Śro", "Czw", "Pią"]
    hours = ["7:30", "9:15", "11:15", "13:15", "15:15", "17:05", "18:45"]
    timetable = defaultdict(lambda: [""] * len(hours))

    for entry in schedule_data:
        ts = entry["timeslot"]
        for day in days:
            if ts.startswith(day):
                hour = ts.split()[1]
                if hour in hours:
                    hour_idx = hours.index(hour)
                    line = f"{entry['course_id']}\n{entry['teacher']}\n{entry['room']}"
                    timetable[day][hour_idx] += line + "\n"

    # Create visual table
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_axis_off()

    table_data = []
    for i, hour in enumerate(hours):
        row = [hour]
        for day in days:
            cell = timetable[day][i].strip()
            row.append(cell)
        table_data.append(row)

    col_labels = ["Hour"] + days
    table = ax.table(cellText=table_data, colLabels=col_labels, loc='center', cellLoc='left')
    table.scale(1, 2)
    table.auto_set_font_size(False)
    table.set_fontsize(8)

    plt.title(f"Schedule for {label_type}: {label}", fontsize=14)
    plt.tight_layout()

    if image_path:
        plt.savefig(image_path, dpi=300)
        print(f"Saved schedule to {image_path}")
    else:
        plt.show()


def get_group_schedule_data(individual, group_code, c_s, t_s, r_s, ts_s):
    """
    Extract schedule entries for a group. Returns structured data suitable for visualization.
    """
    c, t, r, ts = individual.shape
    schedule = []

    for ts_idx in range(ts):
        for c_idx in range(c):
            if group_code not in c_s[c_idx]:
                continue
            for t_idx in range(t):
                for r_idx in range(r):
                    if individual[c_idx, t_idx, r_idx, ts_idx]:
                        schedule.append({
                            "course_id": c_s[c_idx],
                            "teacher": t_s[t_idx],
                            "room": r_s[r_idx],
                            "timeslot": ts_s[ts_idx]
                        })
    return schedule

def get_room_schedule_data(individual, room_idx, c_s, t_s, r_s, ts_s):
    """
    Returns schedule entries for a room as a list of dicts.
    """
    c, t, r, ts = individual.shape
    schedule = []

    for ts_idx in range(ts):
        for c_idx in range(c):
            for t_idx in range(t):
                if individual[c_idx, t_idx, room_idx, ts_idx]:
                    schedule.append({
                        "course_id": c_s[c_idx],
                        "teacher": t_s[t_idx],
                        "room": r_s[room_idx],
                        "timeslot": ts_s[ts_idx]
                    })
    return schedule


def get_teacher_schedule_data(individual, teacher_idx, c_s, t_s, r_s, ts_s):
    """
    Returns schedule entries for a teacher as a list of dicts.
    """
    c, t, r, ts = individual.shape
    schedule = []

    for ts_idx in range(ts):
        for c_idx in range(c):
            for r_idx in range(r):
                if individual[c_idx, teacher_idx, r_idx, ts_idx]:
                    schedule.append({
                        "course_id": c_s[c_idx],
                        "teacher": t_s[teacher_idx],
                        "room": r_s[r_idx],
                        "timeslot": ts_s[ts_idx]
                    })
    return schedule


if __name__ == "__main__":
    # Load data
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

    population = np.load("population-elo.npz")["population"]
    individual = population[:, :, :, :, 0]  # extract single individual
    # Load the best individual solution matrix

    data = np.load("best.npz")
    best = data['best']
    


    '''
    #find_top_teachers_and_print_schedules(best, courses, teachers, rooms, time_slots, top_n=10)
    find_top_teachers_and_print_schedules(individual, courses, teachers, rooms, time_slots, top_n=10)
    find_top_rooms_and_print_schedules(individual, courses, teachers, rooms, time_slots, top_n=10)
    
    # Example: print schedule for "Pon 7:30"
    print_timeslot_schedule(individual, "Pon 7:30", courses, teachers, rooms, time_slots)
    '''

    # Print all classes for group "IST-SI"
    #print_group_schedule(individual, "IST-SI", courses, teachers, rooms, time_slots)

    '''
    # Extract schedule data
    schedule_data = get_group_schedule_data(individual, "IST-SI", courses, teachers, rooms, time_slots)

    # Visualize it
    plot_schedule_from_data(schedule_data, "IST-SI")'''


    # Load a specific teacher schedule
    t_idx = teachers.index("Marek Woda")
    teacher_schedule = get_teacher_schedule_data(individual, t_idx, courses, teachers, rooms, time_slots)
    plot_schedule_from_data(teacher_schedule, "Marek Woda")

    '''
    # Load a specific teacher schedule
    t_idx = teachers.index("Marek Woda")
    teacher_schedule = get_teacher_schedule_data(best, t_idx, courses, teachers, rooms, time_slots)
    plot_schedule_from_data(teacher_schedule, "Marek Woda")'''
    '''
    # Load a specific room schedule
    r_idx = rooms.index("022")
    room_schedule = get_room_schedule_data(individual, r_idx, courses, teachers, rooms, time_slots)
    plot_schedule_from_data(room_schedule, "Room 022")'''









