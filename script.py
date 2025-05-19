import json
import numpy as np
from random import random, shuffle, randint
from bisect import bisect_left
from itertools import accumulate


def open_json(file_name):
    with open(file_name, 'r', encoding='utf-8') as file:
        d = json.load(file)
    return d


def room_conflicts_constraint(sol):
    """ Jeden pokój nie może być przypisany więcej niż raz z tym samym czasie. """
    return np.all(sol.sum(axis=(0, 1)) <= 1)


def teacher_conflicts_constraint(sol):
    """ Jeden prowadzący nie może być przypisany więcej niż raz w tym samym czasie. """
    return np.all(sol.sum(axis=(0, 2)) <= 1)


def all_courses_assigned_once_constraint(sol):
    """ Każdy kurs musi zostać przypisany dokładnie 1 raz. """
    return np.all(sol.sum(axis=(1, 2, 3)) == 1)


def courses_assigned_to_teachers_constraint(sol, c, t, c_t_mapping):
    """ Kurs może być prowadzony tylko przez konkretnych prowadzących. """
    for course_idx in range(len(c)):
        course_code = c[course_idx]
        allowed_teachers = c_t_mapping.get(course_code, [])
        for teacher_idx in range(t):
            teacher_name = t[teacher_idx]
            if teacher_name not in allowed_teachers:
                if np.any(sol[course_idx, teacher_idx, :, :] == 1):
                    return False
    return True


def count_gaps(sol):
    """ Funkcja liczy sumę 'okienek' w planie prowadzących. """

    c, t, r, ts = sol.shape
    time_slots_per_day = int(ts / 5)
    gaps_per_teacher = np.zeros(t, dtype=int)

    for i in range(t):
        teacher_times = sol[:, i, :, :].sum(axis=(0, 1)) > 0

        for d in range(5):
            daily_slots = teacher_times[d*time_slots_per_day:(d + 1)*time_slots_per_day]

            if np.any(daily_slots):
                first = np.argmax(daily_slots)
                last = len(daily_slots) - 1 - np.argmax(daily_slots[::-1])
                between = daily_slots[first:last+1]
                gaps_per_teacher[i] += np.sum(~between)

    return gaps_per_teacher.sum()


def courses_standard_deviation(sol):
    """ Odchylenie standardowe liczby kursów w tygodniu. """
    _, _, _, ts = sol.shape
    time_slots_per_day = int(ts / 5)
    daily_counts = [
        np.sum(sol[d*time_slots_per_day: (d+1)*time_slots_per_day])
        for d in range(5)
    ]
    return np.std(daily_counts)


def fitness(sol):
    """ Funkcja celu. """
    return count_gaps(sol) + courses_standard_deviation(sol)


def genetic_algorithm(c, t, r, ts, c_t_mapping, generations, population_size, mutation_rate):

    print(f"len(c) = {len(c)}")
    print(f"len(t) = {len(t)}")
    print(f"len(r) = {len(r)}")
    print(f"len(ts) = {len(ts)}")

    if population_size % 2:
        print("Rozmiar populacji powinien być parzysty.")
        return

    population = [np.random.randint(0, 2, size=(len(c), len(t), len(r), len(ts))) for _ in range(population_size)]

    best_individual = None
    best_ind_value = 999_999_999

    for i in range(generations):
        print(f"generacja {i}")

        # ewaluacja
        print("ewaluacja")
        fitness_values = [fitness(individual) for individual in population]
        if best_ind_value > min(fitness_values):
            best_individual = population[fitness_values.index(min(fitness_values))]

        # selekcja
        print("selekcja")
        total_fitness = sum(fitness_values)
        fitness_normalized = [f / total_fitness for f in fitness_values]
        cumulative_fitness = list(accumulate(fitness_normalized))
        population = [(population[bisect_left(cumulative_fitness, random())]) for _ in range(population_size)]

        # krzyżowanie
        print("krzyżowanie")
        shuffle(population)
        for j in range(0, population_size - 1, 2):
            crossover_point = randint(1, len(ts))
            temp = population[j][:, :, :, crossover_point:].copy()
            population[j][:, :, :, crossover_point:] = population[j + 1][:, :, :, crossover_point:]
            population[j + 1][:, :, :, crossover_point:] = temp

        # mutacja
        print("mutacja")
        for ind in population:
            for _ in range(int(np.prod((len(c), len(t), len(r), len(ts))) * mutation_rate)):
                j1 = np.random.randint(0, len(c))
                j2 = np.random.randint(0, len(t))
                j3 = np.random.randint(0, len(r))
                j4 = np.random.randint(0, len(ts))
                ind[j1, j2, j3, j4] ^= 1

    fitness_values = [fitness(individual) for individual in population]
    if best_ind_value > min(fitness_values):
        best_individual = population[fitness_values.index(min(fitness_values))]

    return best_individual


if __name__ == "__main__":

    data = open_json("USOS_API_data/final json/FINAL_all_data_combined.json")
    courses = data["courses"]
    teachers = data["lecturers"]
    rooms = data["rooms"]
    time_slots = [
        "Pon 7:30", "Pon 9:15", "Pon 11:15", "Pon 13:15", "Pon 15:15", "Pon 17:05", "Pon 18:45",
        "Wto 7:30", "Wto 9:15", "Wto 11:15", "Wto 13:15", "Wto 15:15", "Wto 17:05", "Wto 18:45",
        "Śro 7:30", "Śro 9:15", "Śro 11:15", "Śro 13:15", "Śro 15:15", "Śro 17:05", "Śro 18:45",
        "Czw 7:30", "Czw 9:15", "Czw 11:15", "Czw 13:15", "Czw 15:15", "Czw 17:05", "Czw 18:45",
        "Pią 7:30", "Pią 9:15", "Pią 11:15", "Pią 13:15", "Pią 15:15", "Pią 17:05", "Pią 18:45",
    ]

    c_t_mapping_data = open_json("USOS_API_data/final json/course_lecturer_mapping.json")

    solution = genetic_algorithm(
        c=courses,
        t=teachers,
        r=rooms,
        ts=time_slots,
        c_t_mapping=c_t_mapping_data,
        generations=100,
        population_size=10,
        mutation_rate=0.001,
    )


"""
TODO:
- jakakolwiek walidacja / wizualizacja (wyprintowanie planu dla każdego przypisanego prowadzącego)

- losowanie populacji spełniającej ograniczenia
- mutacja spełniająca ograniczenia
- krzyżowanie spełniające ograniczenia??
- funkcja celu (ograniczenia miękkie + ograniczenia twarde w formie kary stałej lub w formie kary za każde naruszenie / w innej formie)
- testy, wykresy
"""

