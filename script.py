import json
import random
import numpy as np


def open_json(file_name):
    with open(file_name, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data


def fitness():
    pass


def genetic_algorithm(c, t, r, ts, sg, generations, population_size, mutation_rate):
    population = [np.random.randint(0, 2, size=(len(c), len(t), len(r), len(ts), len(sg))) for _ in range(population_size)]
    print(population)

    for i in range(generations):
        # ewaluacja
        fitness_values = []
        for j in range(population_size):
            fitness_values.append(fitness(population[j]))
            print(fitness_values)
        # selekcja
        # krzyżowanie
        # mutacja
    return 1


if __name__ == "__main__":

    courses = ["kurs1", "kurs2", "kurs3"]
    teachers = ["a", "b", "c"]
    rooms = ["1", "2", "3"]
    time_slots = ["7:30", "9:15", "11:15"]
    students_groups = ["A", "B", "C"]

    solution = genetic_algorithm(
        c=courses,
        t=teachers,
        r=rooms,
        ts=time_slots,
        sg=students_groups,
        generations=100,
        population_size=10,
        mutation_rate=0.1,
    )
