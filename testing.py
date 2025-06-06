import numpy as np
import time
from optimization import *


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

    c_g_mapping = {c_idx: [] for c_idx in range(len(courses))}
    for g, courses_in_group in groups_courses_mapping.items():
        for c_idx in courses_in_group:
            c_g_mapping[c_idx].append(g)

    elo = generate_population_satisfying_constraints(
        c=len(courses),
        t=len(teachers),
        r=len(rooms),
        ts=len(time_slots),
        population_size=1,
        c_t_mapping=course_teacher_mapping,
        c_r_mapping=courses_rooms_mapping,
        g_c_mapping=groups_courses_mapping,
        c_g_mapping=c_g_mapping,
    )

    t0 = time.time()
    np.savez_compressed('population-elo.npz', population=elo)
    print(time.time() - t0)

    t0 = time.time()
    population = np.load("population-elo.npz")["population"]
    print(time.time() - t0)

    print_numbers(*population.shape)
    print_constraints_values(population[:, :, :, :, 0], groups_courses_mapping, course_teacher_mapping, courses_rooms_mapping)
