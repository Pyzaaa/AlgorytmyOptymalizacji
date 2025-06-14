import json
import numpy as np
import random
from bisect import bisect_left
from itertools import accumulate
import time
import pickle
import os
from concurrent.futures import ThreadPoolExecutor


def open_json(file_name):
    with open(file_name, 'r', encoding='utf-8') as file:
        d = json.load(file)
    return d


def create_c_t_mapping(data, c_s, t_s):
    """
        Wstępna transformacja informacji kurs->prowadzący.
    """
    mapping = {}
    course_to_index = {course: idx for idx, course in enumerate(c_s)}
    teacher_to_index = {teacher: idx for idx, teacher in enumerate(t_s)}
    for course, information in data.items():
        if course_to_index.get(course, -1) != -1:
            mapping[course_to_index[course]] = [teacher_to_index[teacher] for teacher in information["lecturers"]]
    return mapping


def create_c_r_mapping(r_data, c_data, r_s, c_s):
    """
        Wstępna transformacja informacji kurs->pokój.
    """
    class_type_to_room_type = {
        "wykład": ["SALA_WYK_MALA"],
        "ćwiczenia": ["SALA_CW"],
        "laboratorium": ["LAB_SPEC", "LAB_KOMP"],
        "projekt": ["LAB_SPEC", "LAB_KOMP", "SALA_CW"],
        "seminarium": ["SALA_SEM", "SALA_WYK_MALA"],
    }
    room_name_to_idx = {room: idx for idx, room in enumerate(r_s)}
    class_types_rooms_mapping = {}
    for class_type, room_type_list in class_type_to_room_type.items():
        class_types_rooms_mapping[class_type] = [
            room_name_to_idx[room]
            for room_type in room_type_list
            for room in r_data.get(room_type, [])
        ]
    mapping = {}
    for idx, course in enumerate(c_s):
        mapping[idx] = class_types_rooms_mapping.get(c_data[course]["class_type"], []).copy()
    return mapping


def create_g_c_mapping(data, c_s):
    """
        Wstępna transformacja informacji grupa->kurs.
    """
    mapping = {}
    for idx, course in enumerate(c_s):
        group = f'{data[course]["field"]}-{data[course]["degree"]}'
        if group not in mapping:
            mapping[group] = []
        mapping[group].append(idx)
    return mapping


def print_numbers(c, t, r, ts, n):
    """
        Wypisanie wymiarów macierzy.
    """
    print(f"kursy: {c}")
    print(f"prowadzący: {t}")
    print(f"pokoje: {r}")
    print(f"okna czasowe: {ts}")
    print()


def print_constraints_values(sol, g_c_mapping, c_t_mapping, c_r_mapping):
    """
        Wypisanie liczby naruszeń wszystkich ograniczeń
    """
    print("NARUSZENIA OGRANICZEŃ")
    print("pokój więcej niż raz")
    print(room_conflicts_constraint_n(sol))
    print("prowadzący więcej niż raz")
    print(teacher_conflicts_constraint_n(sol))
    print("grupa studencka więcej niż raz")
    print(student_groups_conflicts_constraint_n(sol, g_c_mapping))
    print("kurs nieprzypisany lub więcej niż raz")
    print(all_courses_assigned_once_constraint_n(sol))
    print("nieprawidłowy prowadzący")
    print(courses_assigned_to_teachers_constraint_n(sol, c_t_mapping))
    print("nieprawidłowy pokój")
    print(courses_assigned_to_rooms_constraint_n(sol, c_r_mapping))


def room_conflicts_constraint(sol):
    """
        Jeden pokój nie może być przypisany więcej niż jeden raz z tym samym czasie.
    """
    return np.all(sol.sum(axis=(0, 1)) <= 1)


def room_conflicts_constraint_n(sol):
    """
        Jeden pokój nie może być przypisany więcej niż jeden raz z tym samym czasie.
        Zwraca liczbę naruszeń ograniczenia.
    """
    return np.maximum(0, sol.sum(axis=(0, 1)) - 1).sum()


def teacher_conflicts_constraint(sol):
    """
        Jeden prowadzący nie może być przypisany więcej niż jeden raz w tym samym czasie.
    """
    return np.all(sol.sum(axis=(0, 2)) <= 1)


def teacher_conflicts_constraint_n(sol):
    """
        Jeden prowadzący nie może być przypisany więcej niż jeden raz w tym samym czasie.
        Zwraca liczbę naruszeń ograniczenia.
    """
    return np.maximum(0, sol.sum(axis=(0, 2)) - 1).sum()


def student_groups_conflicts_constraint(sol, g_c_mapping):
    """
        Jeda grupa studencka nie może mieć więcej niż jeden kurs w tym samym momencie.
    """
    sol_reduced = sol.sum(axis=(1, 2))
    for g in g_c_mapping.keys():
        if np.any(sol_reduced[g_c_mapping[g], :].sum(axis=0) > 1):
            return False
    return True


def student_groups_conflicts_constraint_n(sol, g_c_mapping):
    """
        Jeda grupa studencka nie może mieć więcej niż jeden kurs w tym samym momencie.
        Zwraca liczbę naruszeń ograniczenia.
    """
    sol_reduced = sol.sum(axis=(1, 2))
    total = 0
    for g in g_c_mapping.keys():
        total += np.maximum(0, sol_reduced[g_c_mapping[g], :].sum(axis=0) - 1).sum()
    return total


def all_courses_assigned_once_constraint(sol):
    """
        Każdy kurs musi zostać przypisany dokładnie jeden raz.
    """
    return np.all(sol.sum(axis=(1, 2, 3)) == 1)


def all_courses_assigned_once_constraint_n(sol):
    """
        Każdy kurs musi zostać przypisany dokładnie jeden raz.
        Zwraca liczbę naruszeń ograniczenia.
    """
    return np.abs(sol.sum(axis=(1, 2, 3)) - 1).sum()


def courses_assigned_to_teachers_constraint(sol, c_t_mapping):
    """
        Kurs może być prowadzony tylko przez konkretnych prowadzących.
    """
    sol_reduced = sol.sum(axis=(2, 3))
    for c_idx in range(sol_reduced.shape[0]):
        if not np.all(np.isin(np.nonzero(sol_reduced[c_idx])[0], c_t_mapping.get(c_idx, []))):
            return False
    return True


def courses_assigned_to_teachers_constraint_n(sol, c_t_mapping):
    """
        Kurs może być prowadzony tylko przez konkretnych prowadzących.
        Zwraca liczbę naruszeń ograniczenia.
    """
    sol_reduced = sol.sum(axis=(2, 3))
    total = 0
    for c_idx in range(sol_reduced.shape[0]):
        total += np.sum(~np.isin(np.nonzero(sol_reduced[c_idx])[0], c_t_mapping.get(c_idx, [])))
    return total


def courses_assigned_to_rooms_constraint(sol, c_r_mapping):
    """
        Kurs musi być prowadzony w salach odpowiadających typowi kursu.
    """
    sol_reduced = sol.sum(axis=(1, 3))
    for c_idx in range(sol_reduced.shape[0]):
        if not np.all(np.isin(np.nonzero(sol_reduced[c_idx])[0], c_r_mapping.get(c_idx, []))):
            return False
    return True


def courses_assigned_to_rooms_constraint_n(sol, c_r_mapping):
    """
        Kurs musi być prowadzony w salach odpowiadających typowi kursu.
        Zwraca liczbę naruszeń ograniczenia.
    """
    sol_reduced = sol.sum(axis=(1, 3))
    total = 0
    for c_idx in range(sol_reduced.shape[0]):
        total += np.sum(~np.isin(np.nonzero(sol_reduced[c_idx])[0], c_r_mapping.get(c_idx, [])))
    return total


def count_teaching_days(sol):
    """
    Count total number of days each teacher is scheduled to teach.
    """
    _, t, _, ts = sol.shape
    sol_reduced = sol.sum(axis=(0, 2))  # shape: (t, ts)
    time_slots_per_day = int(ts / 5)
    teaching_days_per_teacher = np.zeros(t, dtype=int)

    for i in range(t):
        teacher_times = sol_reduced[i, :] > 0
        for d in range(5):
            daily_slots = teacher_times[d * time_slots_per_day:(d + 1) * time_slots_per_day]
            if np.any(daily_slots):
                teaching_days_per_teacher[i] += 1

    return teaching_days_per_teacher.sum()


def count_early_assignments(sol):
    """
    Penalize early classes:
    - Full penalty for slot 0 of each day.
    - Half penalty for slot 1 of each day.
    """
    _, t, _, ts = sol.shape
    sol_reduced = sol.sum(axis=(0, 2))  # shape: (t, ts)
    time_slots_per_day = int(ts / 5)
    early_penalty = 0.0

    for i in range(t):  # For each teacher
        for d in range(5):  # 5 weekdays
            day_start = d * time_slots_per_day
            if sol_reduced[i, day_start] > 0:
                early_penalty += 1.0  # Full penalty for slot 0
            if sol_reduced[i, day_start + 1] > 0:
                early_penalty += 0.5  # Half penalty for slot 1

    return early_penalty


def count_room_changes(sol):
    """
    Penalizes room changes for teachers across their daily schedules.
    """
    _, t, r, ts = sol.shape
    time_slots_per_day = int(ts / 5)
    penalty = 0

    for teacher in range(t):
        for day in range(5):
            day_start = day * time_slots_per_day
            day_end = (day + 1) * time_slots_per_day

            # Get teacher's schedule for the day across rooms
            teacher_day = sol[:, teacher, :, day_start:day_end]  # shape: (c, r, slots)
            room_assignments = np.argmax(teacher_day.sum(axis=0), axis=0)  # shape: (slots,)
            active_slots = teacher_day.sum(axis=(0, 1)) > 0  # bool mask of teaching slots

            prev_room = None
            for slot, active in enumerate(active_slots):
                if not active:
                    continue
                current_room = room_assignments[slot]
                if prev_room is not None and current_room != prev_room:
                    penalty += 1
                prev_room = current_room

    return penalty


def count_gaps(sol):
    """
        Funkcja liczy sumę 'okienek' w planie prowadzących.
    """
    _, t, _, ts = sol.shape
    sol_reduced = sol.sum(axis=(0, 2))
    time_slots_per_day = int(ts / 5)
    gaps_per_teacher = np.zeros(t, dtype=int)
    for i in range(t):
        teacher_times = sol_reduced[i, :] > 0
        for d in range(5):
            daily_slots = teacher_times[d*time_slots_per_day:(d + 1)*time_slots_per_day]
            if np.any(daily_slots):
                first = np.argmax(daily_slots)
                last = len(daily_slots) - 1 - np.argmax(daily_slots[::-1])
                gaps_per_teacher[i] += np.sum(~daily_slots[first:last+1])
    return gaps_per_teacher.sum()


def count_group_gaps(sol, g_c_mapping):
    """
    Optimized calculation of total gaps ('okienka') for student groups per day.

    Parameters:
        sol: np.array, shape (c, t, r, ts)
        g_c_mapping: dict of group_index -> list of course indices

    Returns:
        Total number of gaps (int)
    """
    c, t, r, ts = sol.shape
    time_slots_per_day = ts // 5
    total_gaps = 0

    for group_courses in g_c_mapping.values():
        if not group_courses:
            continue
        # Compute group schedule across all rooms and teachers
        group_schedule = sol[group_courses].sum(axis=(1, 2))  # shape: (len(courses), ts)
        group_schedule = np.any(group_schedule > 0, axis=0)   # shape: (ts,)

        for day in range(5):
            day_start = day * time_slots_per_day
            day_end = (day + 1) * time_slots_per_day
            daily_slots = group_schedule[day_start:day_end]

            if np.any(daily_slots):
                first = np.argmax(daily_slots)
                last = len(daily_slots) - 1 - np.argmax(daily_slots[::-1])
                total_gaps += np.sum(~daily_slots[first:last+1])

    return int(total_gaps)


def count_preference_penalty_sparse(sol, teacher_preferences):
    """
    teacher_preferences should be a preloaded dictionary:
    { "0": { "12": 1, "20": 5, ... }, ... }
    """
    _, t, _, ts = sol.shape
    teacher_time_assignments = sol.sum(axis=(0, 2)) > 0  # shape: (t, ts)

    penalty = 0.0

    for teacher_idx in range(t):
        t_key = str(teacher_idx)
        if t_key not in teacher_preferences:
            continue

        prefs = teacher_preferences[t_key]
        for ts_key, pref_score in prefs.items():
            ts_idx = int(ts_key)
            if teacher_time_assignments[teacher_idx, ts_idx]:
                penalty += 1.0 - (int(pref_score) / 5.0)

    return penalty


def count_group_room_changes(sol, g_c_mapping):
    """
    Optimized penalty calculation for room changes per student group per day.

    Parameters:
        sol: np.array, shape (c, t, r, ts)
        g_c_mapping: dict of group_index -> list of course indices

    Returns:
        Total penalty (int)
    """
    c, t, r, ts = sol.shape
    time_slots_per_day = ts // 5
    penalty = 0

    for group_courses in g_c_mapping.values():
        if not group_courses:
            continue
        # Precompute total schedule for the group: sum over teachers
        group_schedule = sol[group_courses].sum(axis=1)  # shape: (len(courses), r, ts)
        group_schedule = group_schedule.sum(axis=0)      # shape: (r, ts)

        for day in range(5):
            day_start = day * time_slots_per_day
            day_end = (day + 1) * time_slots_per_day

            day_sched = group_schedule[:, day_start:day_end]  # shape: (r, slots)
            room_per_slot = np.argmax(day_sched, axis=0)      # shape: (slots,)
            active_slots = np.any(day_sched > 0, axis=0)       # shape: (slots,)

            # Get active room sequence
            active_rooms = room_per_slot[active_slots]
            if len(active_rooms) > 1:
                # Count room changes by comparing adjacent room assignments
                penalty += np.sum(active_rooms[1:] != active_rooms[:-1])

    return int(penalty)


def fitness(sol, c_t_mapping, c_r_mapping, g_c_mapping, w=(2.0, 2.0, 1.0, 1.0, 1.0), teacher_preferences=None):
    """
    w[0]: gaps
    w[1]: teacher time preference penalties
    w[2]: room changes
    """
    gap_score = count_gaps(sol)
    if teacher_preferences:
        preference_penalty = count_preference_penalty_sparse(sol, teacher_preferences)
    else:
        preference_penalty = 0
    room_change_penalty = count_room_changes(sol)
    group_room_change_penalty = count_group_room_changes(sol, g_c_mapping)
    group_gaps = count_group_gaps(sol, g_c_mapping)

    return (
        w[0] * gap_score +
        w[1] * group_gaps +
        w[2] * preference_penalty +
        w[3] * room_change_penalty +
        w[4] * group_room_change_penalty
    )


# Top-level helper functions (outside any other function)
def compute_gaps_wrapper(sol):
    return count_gaps(sol)


def compute_group_gaps_wrapper(sol, g_c_mapping):
    return count_group_gaps(sol, g_c_mapping)


def compute_preferences_wrapper(sol, teacher_preferences):
    return count_preference_penalty_sparse(sol, teacher_preferences) if teacher_preferences else 0


def compute_teacher_room_changes_wrapper(sol):
    return count_room_changes(sol)


def compute_group_room_changes_wrapper(sol, g_c_mapping):
    return count_group_room_changes(sol, g_c_mapping)


def parallel_fitness(sol, c_t_mapping, c_r_mapping, g_c_mapping, w=(3.0, 2.0, 1.0, 1.0, 0.3), teacher_preferences=None, verbose=False):
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            'gaps': executor.submit(compute_gaps_wrapper, sol),
            'group_gaps': executor.submit(compute_group_gaps_wrapper, sol, g_c_mapping),
            'prefs': executor.submit(compute_preferences_wrapper, sol, teacher_preferences),
            'room_changes': executor.submit(compute_teacher_room_changes_wrapper, sol),
            'group_room_changes': executor.submit(compute_group_room_changes_wrapper, sol, g_c_mapping),
        }

        results = {k: f.result() for k, f in futures.items()}

    if verbose:
        print(results)

    return (
        w[0] * results['gaps'] +
        w[1] * results['group_gaps'] +
        w[2] * results['prefs'] +
        w[3] * results['room_changes'] +
        w[4] * results['group_room_changes']
    )


def get_occupied_table(t, r, ts, g_c_mapping):
    """
        Funkcja tworząca słownik z tablicami zajęcia.
    """
    return {
        't': np.zeros((t, ts), dtype=bool),
        'r': np.zeros((r, ts), dtype=bool),
        'g': {g: np.zeros(ts, dtype=bool) for g in g_c_mapping.keys()}
    }


def course_assignment(sol, c_idx, occ, a, c_g_mapping):
    """
        Funkcja przypisująca kurs oraz zapisująca tablice zajęcia.
    """
    t_idx, r_idx, ts_idx = a
    sol[c_idx, t_idx, r_idx, ts_idx] = True
    occ['t'][t_idx, ts_idx] = True
    occ['r'][r_idx, ts_idx] = True
    for g in c_g_mapping[c_idx]:
        occ['g'][g][ts_idx] = True
    return sol, occ


def random_possible_course_assignment(sol, c_idx, occ, c_t_mapping, c_r_mapping, c_g_mapping):
    """
        Funkcja losująca przypisanie dla danego kursu z listy możliwych przypisań.
    """
    allowed_t = c_t_mapping[c_idx]
    allowed_r = c_r_mapping[c_idx]
    groups = c_g_mapping[c_idx]
    possible = []
    for t_idx in allowed_t:
        for r_idx in allowed_r:
            for ts_idx in range(occ['r'].shape[1]):
                if not occ['r'][r_idx, ts_idx] and not occ['t'][t_idx, ts_idx]:
                    if all(not occ['g'][g][ts_idx] for g in groups):
                        possible.append((t_idx, r_idx, ts_idx))
    if not possible:
        return sol, occ
    return course_assignment(sol, c_idx, occ, random.choice(possible), c_g_mapping)


def generate_population_satisfying_constraints(c, t, r, ts, population_size, c_t_mapping, c_r_mapping, g_c_mapping, c_g_mapping):
    """
        Populacja generowana w sposób pozwalający wstępnie spełnić ograniczenia.
    """
    population = np.zeros((c, t, r, ts, population_size), dtype=bool)
    for i in range(population_size):
        occ = get_occupied_table(t, r, ts, g_c_mapping)
        for c_idx in range(c):
            population[:, :, :, :, i], occ = random_possible_course_assignment(population[:, :, :, :, i], c_idx, occ, c_t_mapping, c_r_mapping, c_g_mapping)
    return population


def crossover_advanced(population, g_c_mapping, c_t_mapping, c_r_mapping, c_g_mapping):
    """
        Krzyżowanie populacji poprzez losowe dobieranie kursów od rodziców.
    """
    c, t, r, ts, n = population.shape
    new_population = np.zeros_like(population)

    for i in range(0, n, 2):
        parent1 = population[:, :, :, :, i]
        parent2 = population[:, :, :, :, i + 1]
        child1 = np.zeros((c, t, r, ts), dtype=bool)
        child2 = np.zeros((c, t, r, ts), dtype=bool)
        occ1 = get_occupied_table(t, r, ts, g_c_mapping)
        occ2 = get_occupied_table(t, r, ts, g_c_mapping)

        def find_course_assignment(individual, c_idx):
            pos = np.argwhere(individual[c_idx])
            return pos[0] if pos.size > 0 else None

        def is_valid(c_idx, t_idx, r_idx, ts_idx, occ):
            if occ['r'][r_idx, ts_idx]:
                return False
            if occ['t'][t_idx, ts_idx]:
                return False
            for g in c_g_mapping[c_idx]:
                if occ['g'][g][ts_idx]:
                    return False
            return True

        for c_idx in range(c):
            parents = [parent1, parent2]
            np.random.shuffle(parents)
            a1, a2 = find_course_assignment(parents[0], c_idx), find_course_assignment(parents[1], c_idx)

            if a1 is not None and is_valid(c_idx, *a1, occ1):
                child1, occ1 = course_assignment(child1, c_idx, occ1, a1, c_g_mapping)
            elif a2 is not None and is_valid(c_idx, *a2, occ1):
                child1, occ1 = course_assignment(child1, c_idx, occ1, a2, c_g_mapping)
            else:
                child1, occ1 = random_possible_course_assignment(child1, c_idx, occ1, c_t_mapping, c_r_mapping, c_g_mapping)

            if a2 is not None and is_valid(c_idx, *a2, occ2):
                child2, occ2 = course_assignment(child2, c_idx, occ2, a2, c_g_mapping)
            elif a1 is not None and is_valid(c_idx, *a1, occ2):
                child2, occ2 = course_assignment(child2, c_idx, occ2, a1, c_g_mapping)
            else:
                child2, occ2 = random_possible_course_assignment(child2, c_idx, occ2, c_t_mapping, c_r_mapping, c_g_mapping)

        new_population[:, :, :, :, i] = child1
        new_population[:, :, :, :, i + 1] = child2
    return new_population


def fix_unassigned_courses(population, c_t_mapping, c_r_mapping, c_g_mapping, g_c_mapping):
    """
        Próba ponownego przypisania kursów, które wcześniej nie zostały przypisane.
    """
    c, t, r, ts, n = population.shape
    for i in range(n):
        individual = population[:, :, :, :, i]
        occ = get_occupied_table(t, r, ts, g_c_mapping)
        occ['t'] = np.any(np.any(individual, axis=2), axis=0)
        occ['r'] = np.any(np.any(individual, axis=1), axis=0)
        for c_idx in range(c):
            assignment = np.argwhere(individual[c_idx])
            if assignment.size > 0:
                t_idx, r_idx, ts_idx = assignment[0]
                for g in c_g_mapping[c_idx]:
                    occ['g'][g][ts_idx] = True
        for c_idx in range(c):
            if not np.any(individual[c_idx, :, :, :]):
                individual, occ = random_possible_course_assignment(individual, c_idx, occ, c_t_mapping, c_r_mapping, c_g_mapping)
    return population


def mutate_swap_timeslots(population, mutation_rate):
    """
        Mutowanie oparte na zamianie dwóch losowych okien czasowych.
    """
    _, _, _, ts, n = population.shape
    for i in range(n):
        if random.random() < mutation_rate:
            ts_idx1, ts_idx2 = np.random.choice(ts, size=2, replace=False)
            temp = np.copy(population[:, :, :, ts_idx1, i])
            population[:, :, :, ts_idx1, i] = population[:, :, :, ts_idx2, i]
            population[:, :, :, ts_idx2, i] = temp
    return population


def genetic_algorithm(c, t, r, ts, population_size, c_t_mapping, c_r_mapping, g_c_mapping, generations, mutation_rate, saving_every,
                      loaded_population=None, output_dir='output', preferences_path=None):
    if preferences_path:
        with open("teacher_preferences2.json") as f:
            teacher_preferences = json.load(f)

    print_numbers(c, t, r, ts, population_size)

    if population_size % 2:
        print("Rozmiar populacji powinien być parzysty.")
        return

    # Tworzenie pomocniczego c_g_mapping
    c_g_mapping = {c_idx: [] for c_idx in range(c)}
    for g, courses_in_group in g_c_mapping.items():
        for c_idx in courses_in_group:
            c_g_mapping[c_idx].append(g)

    os.makedirs(output_dir, exist_ok=True)

    if loaded_population is not None:
        if loaded_population.shape != (c, t, r, ts, population_size):
            print("Rozmiary podanej populacji nie zgadzają się z podanymi parametrami.")
            return
        population = loaded_population

        # Load saved stats
        try:
            with open(f'{output_dir}/fitness_history.pkl', 'rb') as f:
                fitness_history = pickle.load(f)
            with open(f'{output_dir}/computing_times.pkl', 'rb') as f:
                computing_times = pickle.load(f)
            best_individual = np.load(f'{output_dir}/best.npz')['best']
            # Recalculate best_ind_value if needed
            best_ind_value = fitness(population[:, :, :, :, 0], c_t_mapping, c_r_mapping, g_c_mapping)
            for j in range(population.shape[-1]):
                value = fitness(population[:, :, :, :, j], c_t_mapping, c_r_mapping, g_c_mapping)
                if value < best_ind_value:
                    best_ind_value = value
                    best_individual = population[:, :, :, :, j]
            print("Załadowano poprzednie dane statystyczne.")
        except Exception as e:
            print(f"Nie udało się załadować danych statystycznych: {e}")
            fitness_history = []
            computing_times = []
            best_individual = None
            best_ind_value = float('inf')
    else:
        population = generate_population_satisfying_constraints(c, t, r, ts, population_size, c_t_mapping, c_r_mapping,
                                                                g_c_mapping,
                                                                c_g_mapping)
        fitness_history = []
        computing_times = []
        best_individual = None
        best_ind_value = float('inf')

    # save original pop
    np.savez_compressed(f'{output_dir}/original_population.npz', population=population)

    for i in range(generations):
        print(f"--- generacja {i+1}/{generations} ---")

        # zapis do pliku
        if saving_every and i != 0:
            if i % saving_every == 0:
                np.savez_compressed(f'{output_dir}/population.npz', population=population)
                np.savez_compressed(f'{output_dir}/best.npz', best=best_individual)
                with open(f'{output_dir}/fitness_history.pkl', 'wb') as f:
                    pickle.dump(fitness_history, f)
                with open(f'{output_dir}/computing_times.pkl', 'wb') as f:
                    pickle.dump(computing_times, f)

        time_start = time.time()

        # ewaluacja
        print("ewaluacja")
        fitness_values = [parallel_fitness(population[:, :, :, :, j], c_t_mapping, c_r_mapping, g_c_mapping, teacher_preferences=teacher_preferences) for j in range(population_size)]
        print(fitness_values)
        min_ind_value = min(fitness_values)
        if best_ind_value > min_ind_value:
            best_ind_value = min_ind_value
            best_individual = population[:, :, :, :, fitness_values.index(min_ind_value)]
        print(f"best overall: {best_ind_value}, best this gen: {min_ind_value}, average this gen: {sum(fitness_values) / population_size}")
        fitness_history.append(fitness_values)

        # selekcja
        print("selekcja")   # odwracamy wartości fitness, bo chemy je minimalizować
        fitness_scaled = [max(fitness_values) - f + 1e-2 for f in fitness_values]
        total = sum(fitness_scaled)
        fitness_normalized = [f / total for f in fitness_scaled]
        cumulative_fitness = list(accumulate(fitness_normalized))
        population = population[:, :, :, :, [bisect_left(cumulative_fitness, random.random()) for _ in range(population_size)]]

        # krzyżowanie
        print("krzyżowanie")
        population = crossover_advanced(population, g_c_mapping, c_t_mapping, c_r_mapping, c_g_mapping)

        # naprawianie
        print("naprawianie")
        population = fix_unassigned_courses(population, c_t_mapping, c_r_mapping, c_g_mapping, g_c_mapping)

        # mutacja
        print("mutacja")
        population = mutate_swap_timeslots(population, mutation_rate)

        # zmierzenie czasu
        time_end = time.time() - time_start
        print(f"### generacja {i+1}/{generations} ukończona w czasie {time_end:.2f} sekund\n")
        computing_times.append(time_end)

    # ewaluacja końcowa
    print("ewaluacja końcowa")
    fitness_values = [parallel_fitness(population[:, :, :, :, j], c_t_mapping, c_r_mapping, g_c_mapping, teacher_preferences=teacher_preferences, verbose=True) for j in range(population_size)]
    print(fitness_values)
    min_ind_value = min(fitness_values)
    if best_ind_value > min_ind_value:
        best_ind_value = min_ind_value
        best_individual = population[:, :, :, :, fitness_values.index(min_ind_value)]
    print(f"best overall: {best_ind_value}, best this gen: {min_ind_value}, average this gen: {sum(fitness_values) / population_size}")
    fitness_history.append(fitness_values)

    # zapis końcowy
    np.savez_compressed(f'{output_dir}/population.npz', population=population)
    np.savez_compressed(f'{output_dir}/best.npz', best=best_individual)
    with open(f'{output_dir}/fitness_history.pkl', 'wb') as f:
        pickle.dump(fitness_history, f)
    with open(f'{output_dir}/computing_times.pkl', 'wb') as f:
        pickle.dump(computing_times, f)

    print_constraints_values(best_individual, g_c_mapping, c_t_mapping, c_r_mapping)

    return best_individual


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

    solution = genetic_algorithm(
        c=len(courses),
        t=len(teachers),
        r=len(rooms),
        ts=len(time_slots),
        population_size=20,
        c_t_mapping=course_teacher_mapping,
        c_r_mapping=courses_rooms_mapping,
        g_c_mapping=groups_courses_mapping,
        generations=100,
        mutation_rate=0.15,
        saving_every=5,     # dla False nie zapisuje w ogóle
        #loaded_population=np.load("output/population.npz")["population"],
        preferences_path="teacher_preferences2.json",
    )
