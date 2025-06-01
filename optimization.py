import json
import numpy as np
import random
from bisect import bisect_left
from itertools import accumulate
import time
import pickle


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


def print_numbers(c, t, r, ts, n):
    """
        Wypisanie wymiarów macierzy.
    """
    print(f"kursy: {c}")
    print(f"prowadzący: {t}")
    print(f"pokoje: {r}")
    print(f"okna czasowe: {ts}")
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


def courses_standard_deviation(sol):
    """
        Odchylenie standardowe liczby kursów w tygodniu.
    """
    _, _, _, ts = sol.shape
    time_slots_per_day = int(ts / 5)
    daily_counts = [
        np.sum(sol[d*time_slots_per_day: (d+1)*time_slots_per_day])
        for d in range(5)
    ]
    return np.std(daily_counts)


def fitness(sol, c_t_mapping, c_r_mapping, g_c_mapping, w=(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)):
    """
        Funkcja celu.
    """
    return count_gaps(sol)
    # return (
    #         w[0] * count_gaps(sol) +
    #         w[1] * room_conflicts_constraint_n(sol) +
    #         w[2] * teacher_conflicts_constraint_n(sol) +
    #         w[3] * student_groups_conflicts_constraint_n(sol, g_c_mapping) +
    #         w[4] * all_courses_assigned_once_constraint_n(sol) +
    #         w[5] * courses_assigned_to_teachers_constraint_n(sol, c_t_mapping) +
    #         w[6] * courses_assigned_to_rooms_constraint_n(sol, c_r_mapping)
    # )


def generate_population(c, t, r, ts, population_size):
    """
        Zupełnie losowo generowana populacja.
    """
    return np.random.randint(0, 2, size=(c, t, r, ts, population_size))


def generate_population_satisfying_constraints(c, t, r, ts, population_size, c_t_mapping, c_r_mapping, g_c_mapping):
    """
        Populacja generowana w sposób pozwalający wstępnie spełnić ograniczenia.
    """
    population = np.zeros((c, t, r, ts, population_size), dtype=bool)

    c_g_mapping = {course_idx: [] for course_idx in range(c)}
    for g, courses_in_group in g_c_mapping.items():
        for c_idx in courses_in_group:
            c_g_mapping[c_idx].append(g)

    for i in range(population_size):
        r_occupied = np.zeros((r, ts), dtype=bool)
        t_occupied = np.zeros((t, ts), dtype=bool)
        g_occupied = {g: np.zeros(ts, dtype=bool) for g in g_c_mapping.keys()}

        for c_idx in range(c):
            allowed_t = c_t_mapping[c_idx]
            allowed_r = c_r_mapping[c_idx]
            g_of_course = c_g_mapping[c_idx]

            possible_assignments = []
            for t_idx in allowed_t:
                for r_idx in allowed_r:
                    for ts_idx in range(ts):
                        if (not r_occupied[r_idx, ts_idx]
                            and not t_occupied[t_idx, ts_idx]
                                and all(not g_occupied[g][ts_idx] for g in g_of_course)):
                            possible_assignments.append((t_idx, r_idx, ts_idx))

            if not possible_assignments:
                print(f"Nie znaleziono dopuszczalnego przypisania dla kursu: {c_idx}")
            else:
                t_idx, r_idx, ts_idx = random.choice(possible_assignments)
                population[c_idx, t_idx, r_idx, ts_idx, i] = 1
                r_occupied[r_idx, ts_idx] = True
                t_occupied[t_idx, ts_idx] = True
                for g in g_of_course:
                    g_occupied[g][ts_idx] = True
    return population


def mutate_by_swap(sol, c_t_mapping, c_r_mapping, g_c_mapping, max_attempts=100):
    """
        Mutuje osobnika przez zamianę dwóch przypisań na jeden z czterech sposobów.
    """
    c, t, r, ts = sol.shape
    assignments = np.argwhere(sol == 1)
    swap_type = random.choice(["random", "same_teacher", "same_group", "same_room"])

    for _ in range(max_attempts):
        a1 = random.choice(assignments)
        c1, t1, r1, ts1 = a1

        candidates = []
        for a2 in assignments:
            if np.array_equal(a1, a2):
                continue
            c2, t2, r2, ts2 = a2
            if ts1 == ts2:
                continue
            if swap_type == "same_teacher" and t1 != t2:
                continue
            if swap_type == "same_room" and r1 != r2:
                continue
            if swap_type == "same_group":
                shared = any(c1 in courses and c2 in courses for courses in g_c_mapping.values())
                if not shared:
                    continue
            candidates.append(a2)
        if not candidates:
            continue

        a2 = random.choice(candidates)
        c2, t2, r2, ts2 = a2

        # Sprawdź, czy nowa konfiguracja nauczyciel/pokój jest dopuszczalna
        if (t2 in c_t_mapping[c1] and r2 in c_r_mapping[c1] and
                t1 in c_t_mapping[c2] and r1 in c_r_mapping[c2]):

            # Tymczasowa zamiana
            individual[c1, t1, r1, ts1] = 0
            individual[c2, t2, r2, ts2] = 0
            individual[c1, t2, r2, ts2] = 1
            individual[c2, t1, r1, ts1] = 1

            if (is_valid_assignment(individual, c1, t2, r2, ts2, g_c_mapping, c_t_mapping, c_r_mapping) and
                    is_valid_assignment(individual, c2, t1, r1, ts1, g_c_mapping, c_t_mapping, c_r_mapping)):
                # Zapisz wynik do populacji
                population[:, :, :, :, individual_index] = individual
                return True

            # Cofnij jeśli konflikt
            individual[c1, t2, r2, ts2] = 0
            individual[c2, t1, r1, ts1] = 0
            individual[c1, t1, r1, ts1] = 1
            individual[c2, t2, r2, ts2] = 1

    return False


def genetic_algorithm(c, t, r, ts, population_size, c_t_mapping, c_r_mapping, g_c_mapping, generations, mutation_rate, saving_every,
                      loaded_population=None):

    print_numbers(c, t, r, ts, population_size)

    if population_size % 2:
        print("Rozmiar populacji powinien być parzysty.")
        return

    if loaded_population is not None:
        if loaded_population.shape != (c, t, r, ts, population_size):
            print("Rozmiary podanej populacji nie zgadzają się z podanymi parametrami.")
            return
        population = loaded_population
    else:
        # population = generate_population(c, t, r, ts, population_size)
        population = generate_population_satisfying_constraints(c, t, r, ts, population_size, c_t_mapping, c_r_mapping, g_c_mapping)

    best_individual = None
    best_ind_value = float('inf')

    computing_times = []
    fitness_history = []

    for i in range(generations):
        print(f"--- generacja {i}/{generations} ---")

        # zapis do pliku
        if saving_every:
            if i % saving_every == 0:
                np.savez_compressed('population.npz', population=population)
                np.savez_compressed('best.npz', best=best_individual)
                with open('fitness_history.pkl', 'wb') as f:
                    pickle.dump(fitness_history, f)
                with open('computing_times.pkl', 'wb') as f:
                    pickle.dump(computing_times, f)

        time_start = time.time()

        # ewaluacja
        print("ewaluacja")
        fitness_values = [fitness(population[:, :, :, :, j], c_t_mapping, c_r_mapping, g_c_mapping) for j in range(population_size)]
        print(fitness_values)
        if best_ind_value > min(fitness_values):
            best_individual = population[:, :, :, :, fitness_values.index(min(fitness_values))]
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
        indices = np.arange(population_size)
        np.random.shuffle(indices)
        population = population[:, :, :, :, indices]
        for j in range(0, population_size - 1, 2):
            crossover_point = random.randint(1, ts - 1)
            temp = population[:, :, :, crossover_point:, j].copy()
            population[:, :, :, crossover_point:, j] = population[:, :, :, crossover_point:, j + 1]
            population[:, :, :, crossover_point:, j + 1] = temp

        # mutacja
        print("mutacja")
        for j in range(population_size):
            for _ in range(int(np.prod((c, t, r, ts)) * mutation_rate)):
                j1 = np.random.randint(0, c)
                j2 = np.random.randint(0, t)
                j3 = np.random.randint(0, r)
                j4 = np.random.randint(0, ts)
                population[j1, j2, j3, j4, j] ^= 1

        # zmierzenie czasu
        time_end = time.time() - time_start
        print(f"### generacja {i}/{generations} ukończona w czasie {time_end} sekund")
        computing_times.append(time_end)

    # ewaluacja końcowa
    fitness_values = [fitness(population[:, :, :, :, j], c_t_mapping, c_r_mapping, g_c_mapping) for j in range(population_size)]
    if best_ind_value > min(fitness_values):
        best_individual = population[:, :, :, :, fitness_values.index(min(fitness_values))]
    fitness_history.append(fitness_values)

    # zapis końcowy
    np.savez_compressed('population.npz', population=population)
    np.savez_compressed('best.npz', best=best_individual)
    with open('fitness_history.pkl', 'wb') as f:
        pickle.dump(fitness_history, f)
    with open('computing_times.pkl', 'wb') as f:
        pickle.dump(computing_times, f)

    return best_individual


if __name__ == "__main__":

    course_data = open_json("Final_load_data/merged_filtered_course_data.json")
    rooms_type_mapping_data = open_json("Final_load_data/final_class_type_to_rooms.json")

    # !! importowanie setów powoduje że listy zawsze są inne
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
        population_size=10,
        c_t_mapping=course_teacher_mapping,
        c_r_mapping=courses_rooms_mapping,
        g_c_mapping=groups_courses_mapping,
        generations=10,
        mutation_rate=0.0005,
        saving_every=1,     # dla False nie zapisuje w ogóle
        # loaded_population=np.load("population.npz")["population"],
    )

"""
TODO:
MUTACJA
pomysł 1: zamiana dwóch kursów według czasu
losujemy typ wybierania kursów 1 z 4
1.zupełnie losowe kursy
2.kursy co ten sam prowadzący
3.ta sama grupa studencka
4.ten sam pokój
losujemy 1 kurs i dla niego znajdujemy 2 kurs
sprawdzamy czy ograniczenia bedą spełnione po zamianie ich okien czasowych
jak tak to zamieniamy

pomysł 2: zmienianie jednego parametru (pokoju, prowadzącego, okna czasowego) na inny z możliwych (np. zmiana prowadzącego na innego)
losowanie kursu
sprawdzanie co można w nim zmienić (lista możliwych pokoi, lista możliwych prowadzących, lista okien czasowych)
losujemy jeden z tych trzech list
losowanie jednego parametru z wylosowanej listy
zmiana jednego parametru 


- krzyżowanie spełniające ograniczenia?? (z naprawianiem?)

- co jeżeli w generowaniu wstępnym nie udaje się przypisać kursu??
(usunąć jak jest za dużo kursów na grupę, spróbować przypisać kurs po pierwszej iteracji?)

- wybranie parametrów i f celu
- testy, odpalenie i zobaczenie co się stanie
- ewentualne dostrojenie parametrów (lub danych)
- wizualizacja wyniku
- wczytanie zapisanych danych i analiza, wykresy itd.

- rozwiązać za pomocą solvera np cplex
"""
