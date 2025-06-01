import pickle
import numpy as np

def load_pickle_file(filepath):
    with open(filepath, 'rb') as f:
        return pickle.load(f)

def analyze_fitness_history(fitness_history):
    fitness_history = np.array(fitness_history)
    best_fitness = fitness_history.min(axis=1)
    avg_fitness = fitness_history.mean(axis=1)

    print("📊 Fitness Statistics:")
    print(f" - Generations: {len(fitness_history)}")
    print(f" - Best fitness overall: {best_fitness.min():.4f}")
    print(f" - Best fitness per generation: {best_fitness}")
    print(f" - Average fitness per generation: {avg_fitness}")

def analyze_computing_times(computing_times):
    computing_times = np.array(computing_times)

    print("\n⏱️ Computation Time Statistics:")
    print(f" - Total computation time: {computing_times.sum():.2f} seconds")
    print(f" - Average per generation: {computing_times.mean():.4f} seconds")
    print(f" - Fastest generation: {computing_times.min():.4f} seconds")
    print(f" - Slowest generation: {computing_times.max():.4f} seconds")

def main():
    fitness_history_file = 'fitness_history.pkl'
    computing_times_file = 'computing_times.pkl'

    try:
        fitness_history = load_pickle_file(fitness_history_file)
        computing_times = load_pickle_file(computing_times_file)

        analyze_fitness_history(fitness_history)
        analyze_computing_times(computing_times)

    except FileNotFoundError as e:
        print(f"❌ File not found: {e.filename}")
    except Exception as e:
        print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    main()
