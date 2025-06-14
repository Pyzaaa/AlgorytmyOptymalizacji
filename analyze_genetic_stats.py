import pickle
import numpy as np
import matplotlib.pyplot as plt
import os


def load_pickle_file(filepath):
    with open(filepath, 'rb') as f:
        return pickle.load(f)


def fitness_best(fitness_history):
    return fitness_history.min(axis=1)


def fitness_best_overall(fitness_history):
    min_overall = float('inf')
    result = []
    for fitness_values in fitness_history:
        min_overall = min(min_overall, min(fitness_values))
        result.append(float(min_overall))
    return result


def fitness_average(fitness_history):
    return fitness_history.mean(axis=1)


def analyze_fitness_history(fitness_history):
    fitness_history = np.array(fitness_history)
    best_fitness = fitness_best(fitness_history)
    best_fitness_overall = fitness_best_overall(fitness_history)
    avg_fitness = fitness_average(fitness_history)
    print("Lista wartości funkcji celu w każdej generacji algorytmu:")
    print(fitness_history)
    print()
    print("Statystyki funkcji celu:")
    print(f" - Liczba generacji: {len(fitness_history) - 1}")
    print(f" - Najlepsza wartość funkcji celu: {best_fitness.min():.4f}")
    print(f" - Najlepsza wartość funkcji celu w każdej generacji:\n{best_fitness}")
    print(f" - Najlepsza dotychczasowa wartość funkcji celu w każdej generacji:\n{best_fitness_overall}")
    print(f" - Średnia wartość funkcji celu w każdej generacji:\n{avg_fitness}")
    print()


def analyze_computing_times(computing_times):
    computing_times = np.array(computing_times)
    print("Statystyki czasu pracy algorytmu:")
    print(f" - Całkowity czas: {computing_times.sum():.2f} sekund")
    print(f" - Średni czas na generacje: {computing_times.mean():.2f} sekund")
    print(f" - Najkrótszy czas: {computing_times.min():.2f} sekund w {np.argmin(computing_times)} generacji")
    print(f" - Najdłuższy czas: {computing_times.max():.2f} sekund w {np.argmax(computing_times)} generacji")
    print()


def plot_fitness_chart(data, title="", x_label="", y_label="", image_path=None):
    plt.figure(figsize=(8, 4))
    plt.plot(data[0], linestyle='-', color='orange', label='średnia')
    plt.plot(data[1], linestyle='-', color='blue', label='najlepsza w generacji')
    plt.plot(data[2], linestyle='-', color='green', label='najlepsza dotychczas')
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    if image_path:
        plt.savefig(image_path, dpi=300)
        print(f"Wykres zapisany do {image_path}")
    else:
        plt.show()


def plot_time_chart(data, title="", x_label="", y_label="", image_path=None):
    plt.figure(figsize=(8, 4))
    plt.plot(data, linestyle='-', color='red')
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.grid(True)
    plt.tight_layout()
    if image_path:
        plt.savefig(image_path, dpi=300)
        print(f"Wykres zapisany do {image_path}")
    else:
        plt.show()


if __name__ == "__main__":
    input_dir = "output"
    fitness_history_file_path = input_dir + '/fitness_history.pkl'
    computing_times_file_path = input_dir + '/computing_times.pkl'
    fitness_history = load_pickle_file(fitness_history_file_path)
    computing_times = load_pickle_file(computing_times_file_path)

    try:
        analyze_fitness_history(fitness_history)
        analyze_computing_times(computing_times)
        output_dir = "charts"
        os.makedirs(output_dir, exist_ok=True)
        plot_fitness_chart(
            data=[
                fitness_average(np.array(fitness_history)),
                fitness_best(np.array(fitness_history)),
                fitness_best_overall(np.array(fitness_history)),
            ],
            title="Wartość funkcji celu w każdej generacji",
            x_label="generacja",
            y_label="wartość funkcji celu",
            image_path=f"{output_dir}/fitness.png"
        )
        plot_time_chart(
            data=computing_times,
            title="Czas pracy algorytmu",
            x_label="generacja",
            y_label="czas [s]",
            image_path=f"{output_dir}/times.png"
        )
    except FileNotFoundError as e:
        print(f"File not found: {e.filename}")
    except Exception as e:
        print(f"Error: {e}")
