import numpy as np
import random

def activate_function(x):
    return 1 / (1 + np.exp(-x))


n = int(input("Enter Number of inputs you want:"))

# Initial weights (only once)
weights = np.random.randn(n)

bias = np.random.uniform(0.1, 0.9)

# User inputs
inputs = []
for i in range(n):
    inputs.append(float(input("Enter your input: ")))

inputs = np.array(inputs)

print("\nInitial Weights (First Generation):")
print(weights)

# Crossover (self crossover using split)
crossover_point = random.randint(1, n-1)
child_weights = np.concatenate((weights[:crossover_point], weights[crossover_point:]))

print("\nAfter Crossover:")
print(child_weights)

# Mutation (change one weight)
mutation_index = random.randint(0, n-1)
old_weight = child_weights[mutation_index]
child_weights[mutation_index] += np.random.randn()

print("\nAfter Mutation:")
print(f"Weight {mutation_index} changed from {old_weight} to {child_weights[mutation_index]}")

# Neuron output using evolved weights
z = 0
for i in range(n):
    z += inputs[i] * child_weights[i]

z += bias

print("\nFinal Output:")
print(activate_function(z))
