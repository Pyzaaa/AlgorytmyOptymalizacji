import pickle
import numpy as np


def load_pickle_file(filepath):
    with open(filepath, 'rb') as f:
        return pickle.load(f)


def analyze_fitness_history(fitness_history):
    fitness_history = np.array(fitness_history)
    best_fitness = fitness_history.min(axis=1)
    avg_fitness = fitness_history.mean(axis=1)
    print(fitness_history)
    print("Fitness Statistics:")
    print(f" - Generations: {len(fitness_history) - 1}")
    print(f" - Best fitness overall: {best_fitness.min():.4f}")
    print(f" - Best fitness per generation: {best_fitness}")
    print(f" - Average fitness per generation: {avg_fitness}")
    print()


def analyze_computing_times(computing_times):
    computing_times = np.array(computing_times)
    print("Computation Time Statistics:")
    print(f" - Total computation time: {computing_times.sum():.2f} seconds")
    print(f" - Average per generation: {computing_times.mean():.2f} seconds")
    print(f" - Fastest generation: {computing_times.min():.2f} seconds")
    print(f" - Slowest generation: {computing_times.max():.2f} seconds")
    print()


if __name__ == "__main__":
    output_dir = "output"
    fitness_history_file = output_dir + '/fitness_history.pkl'
    computing_times_file = output_dir + '/computing_times.pkl'

    try:
        analyze_fitness_history(load_pickle_file(fitness_history_file))
        analyze_computing_times(load_pickle_file(computing_times_file))
    except FileNotFoundError as e:
        print(f"File not found: {e.filename}")
    except Exception as e:
        print(f"Error: {e}")
