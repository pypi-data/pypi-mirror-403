import random

def fitness(x):
    return x * x

population = [random.randint(0, 31) for _ in range(6)]

for generation in range(5):
    print("Generation", generation, population)

    fitness_values = [fitness(x) for x in population]

    parents = sorted(population, key=fitness, reverse=True)[:2]

    child1 = (parents[0] + parents[1]) // 2
    child2 = abs(parents[0] - parents[1])

    if random.random() < 0.1:
        child1 = random.randint(0, 31)

    population = parents + [child1, child2] + [random.randint(0, 31)]

best = max(population, key=fitness)
print("Best solution:", best)
print("Best fitness:", fitness(best))
