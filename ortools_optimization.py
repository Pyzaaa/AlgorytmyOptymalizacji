from ortools.sat.python import cp_model
from optimization import open_json, create_c_r_mapping, create_c_t_mapping, create_g_c_mapping
import numpy as np
import json
import os


def extract_to_matrix(solver, c, t, r, ts, dv_teacher, dv_room, dv_timeslot):
    sol = np.zeros((c, t, r, ts), dtype=bool)
    for idx_c in range(c):
        idx_t = solver.Value(dv_teacher[idx_c])
        idx_r = solver.Value(dv_room[idx_c])
        idx_ts = solver.Value(dv_timeslot[idx_c])
        sol[idx_c, idx_t, idx_r, idx_ts] = True
    return sol


def optimization(c, t, r, ts, c_t_mapping, c_r_mapping, c_g_mapping, max_time=120.0, output_dir="output_solver"):

    model = cp_model.CpModel()

    # Struktura zmiennych decyzyjnych zapewnia, że każdy kurs jest przypisany dokładnie 1 raz

    # Dla każdego kursu nauczyciel może być tylko z dostępnych (na podstawie c_t_mapping)
    dv_teacher = [model.NewIntVarFromDomain(cp_model.Domain.FromValues(c_t_mapping[idx_c]), f'teacher_{c}') for idx_c in range(c)]

    # Dla każdego kursu pokój może być tylko z dostępnych (na podstawie c_r_mapping)
    dv_room = [model.NewIntVarFromDomain(cp_model.Domain.FromValues(c_r_mapping[idx_c]), f'room_{c}') for idx_c in range(c)]

    dv_timeslot = [model.NewIntVar(0, ts - 1, f'timeslot_{idx_c}') for idx_c in range(c)]

    # Dla każdych dwóch kursów nie może być w tym samym czasie ten sam nauczyciel, pokój lub grupa studencka
    for idx_c1 in range(c):
        for idx_c2 in range(idx_c1 + 1, c):
            diff_teacher = model.NewBoolVar(f'diff_teacher_{idx_c1}_{idx_c2}')
            diff_room = model.NewBoolVar(f'diff_room_{idx_c1}_{idx_c2}')
            diff_timeslot = model.NewBoolVar(f'diff_timeslot_{idx_c1}_{idx_c2}')
            model.Add(dv_teacher[idx_c1] != dv_teacher[idx_c2]).OnlyEnforceIf(diff_teacher)
            model.Add(dv_teacher[idx_c1] == dv_teacher[idx_c2]).OnlyEnforceIf(diff_teacher.Not())
            model.Add(dv_room[idx_c1] != dv_room[idx_c2]).OnlyEnforceIf(diff_room)
            model.Add(dv_room[idx_c1] == dv_room[idx_c2]).OnlyEnforceIf(diff_room.Not())
            model.Add(dv_timeslot[idx_c1] != dv_timeslot[idx_c2]).OnlyEnforceIf(diff_timeslot)
            model.Add(dv_timeslot[idx_c1] == dv_timeslot[idx_c2]).OnlyEnforceIf(diff_timeslot.Not())
            model.AddBoolOr([diff_teacher, diff_timeslot])
            model.AddBoolOr([diff_room, diff_timeslot])
            if c_g_mapping[idx_c1] == c_g_mapping[idx_c2]:
                model.Add(dv_timeslot[idx_c1] != dv_timeslot[idx_c2])
    print("Ograniczenie 1 nauczyciel i 1 pokój na 1 okno czasowe wprowadzone.")

    d = 5
    s = ts // d
    has_class = {}
    for idx_t in range(t):
        for idx_d in range(d):
            for idx_s in range(s):
                idx_ts = idx_d * s + idx_s
                b = model.NewBoolVar(f'has_class_{idx_t}_{idx_d}_{idx_s}')
                relevant_courses = []
                for idx_c in range(c):
                    if idx_t in c_t_mapping[idx_c]:
                        b1 = model.NewBoolVar(f'c{idx_c}_is_t{idx_t}')
                        b2 = model.NewBoolVar(f'c{idx_c}_is_slot{idx_ts}')
                        course_here = model.NewBoolVar(f'course_{idx_c}_{idx_t}_{idx_ts}')
                        model.Add(dv_teacher[idx_c] == idx_t).OnlyEnforceIf(b1)
                        model.Add(dv_teacher[idx_c] != idx_t).OnlyEnforceIf(b1.Not())
                        model.Add(dv_timeslot[idx_c] == idx_ts).OnlyEnforceIf(b2)
                        model.Add(dv_timeslot[idx_c] != idx_ts).OnlyEnforceIf(b2.Not())
                        model.AddBoolAnd([b1, b2]).OnlyEnforceIf(course_here)
                        model.AddBoolOr([b1.Not(), b2.Not()]).OnlyEnforceIf(course_here.Not())
                        relevant_courses.append(course_here)
                if relevant_courses:
                    model.AddMaxEquality(b, relevant_courses)
                has_class[(idx_t, idx_d, idx_s)] = b
    print("Lista zajęcia prowadzącego w oknach czasowych utworzona.")

    gaps = []
    elo1 = {}
    elo2 = {}
    for idx_t in range(t):
        for idx_d in range(d):
            has_classes = [has_class[(idx_t, idx_d, idx_s)] for idx_s in range(s)]

            has_any = model.NewBoolVar(f'has_any_{idx_t}_{idx_d}')
            model.AddBoolOr(has_classes).OnlyEnforceIf(has_any)
            model.AddBoolAnd([hc.Not() for hc in has_classes]).OnlyEnforceIf(has_any.Not())

            earliest = model.NewIntVar(0, s, f'earliest_{idx_t}_{idx_d}')
            latest = model.NewIntVar(0, s, f'latest_{idx_t}_{idx_d}')

            earliest_vals = []
            for idx_s in range(s):
                val = model.NewIntVar(0, s, f'earliest_val_{idx_t}_{idx_d}_{idx_s}')
                model.Add(val == idx_s).OnlyEnforceIf(has_classes[idx_s])
                model.Add(val == s).OnlyEnforceIf(has_classes[idx_s].Not())
                earliest_vals.append(val)
            model.AddMinEquality(earliest, earliest_vals)

            elo1[(idx_t, idx_d)] = earliest

            latest_vals = []
            for idx_s in range(s):
                val = model.NewIntVar(0, s, f'latest_val_{idx_t}_{idx_d}_{idx_s}')
                model.Add(val == idx_s).OnlyEnforceIf(has_classes[idx_s])
                model.Add(val == 0).OnlyEnforceIf(has_classes[idx_s].Not())
                latest_vals.append(val)
            model.AddMaxEquality(latest, latest_vals)

            elo2[(idx_t, idx_d)] = latest

            total_gap = model.NewIntVar(0, s, f'total_gap_{idx_t}_{idx_d}')
            model.Add(total_gap == (latest - earliest + 1) - sum([has_class[(idx_t, idx_d, idx_s)] for idx_s in range(s)])).OnlyEnforceIf(has_any)
            model.Add(total_gap == 0).OnlyEnforceIf(has_any.Not())
            gaps.append(total_gap)

    print("Funkcja celu liczenia okienek wprowadzona.")

    model.Minimize(sum(gaps))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max_time

    # Ustalone ziarno i liczba wątków dla celów testowych
    solver.parameters.random_seed = 42
    solver.parameters.num_search_workers = 1

    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        if status == cp_model.OPTIMAL:
            print("Znaleziono rozwiązanie OPTYMALNE.")
        else:
            print("Znaleziono rozwiązanie DOPUSZCZALNE.")
        print(f'Wartość funkcji celu: {solver.ObjectiveValue()}')
        print(f'Czas pracy solvera: {solver.WallTime()}')
        for idx_c in range(c):
            print(
                f'Kurs {idx_c}: nauczyciel {solver.Value(dv_teacher[idx_c])},',
                f'pokój {solver.Value(dv_room[idx_c])},',
                f'slot {solver.Value(dv_timeslot[idx_c])}',
            )

        # print("Values of has_class after solve:")
        # for key in has_class:
        #     print(key, solver.Value(has_class[key]))

        best = extract_to_matrix(solver, c, t, r, ts, dv_teacher, dv_room, dv_timeslot)
        # zapis do pliku
        os.makedirs(output_dir, exist_ok=True)
        np.savez_compressed(f'{output_dir}/best.npz', best=best)
        result = {
            "objective_value": solver.ObjectiveValue(),
            "computing_time_seconds": solver.WallTime(),
        }
        with open(f"{output_dir}/results.json", "w") as f:
            json.dump(result, f, indent=4)

    else:
        print("Nie znaleziono rozwiązania.")

    return 0


if __name__ == "__main__":

    course_data = open_json("Final_load_data/merged_filtered_course_data.json")
    rooms_type_mapping_data = open_json("Final_load_data/final_class_type_to_rooms.json")

    # Filtrowanie kursów w celu ograniczenia liczby kursów <-----------
    #allowed_fields = ["ISA", "IST", "INS"]
    #course_data = {key: val for key, val in course_data.items() if val["field"] in allowed_fields}
    course_data = {key: val for key, val in course_data.items()}

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

    print(f"ilość kursów: {len(courses)}")
    print()

    course_teacher_mapping = create_c_t_mapping(course_data, courses, teachers)
    courses_rooms_mapping = create_c_r_mapping(rooms_type_mapping_data, course_data, rooms, courses)
    groups_courses_mapping = create_g_c_mapping(course_data, courses)

    # Tworzenie pomocniczego courses_groups_mapping
    courses_groups_mapping = {c_idx: [] for c_idx in range(len(courses))}
    for g, courses_in_group in groups_courses_mapping.items():
        for c_idx in courses_in_group:
            courses_groups_mapping[c_idx].append(g)

    solution = optimization(
        c=len(courses),
        t=len(teachers),
        r=len(rooms),
        ts=len(time_slots),
        c_t_mapping=course_teacher_mapping,
        c_r_mapping=courses_rooms_mapping,
        c_g_mapping=courses_groups_mapping,
        max_time=3600.0,
    )
