import math
import numpy as np

n=int(input("Enter Number of inputs you want:"))

weights = np.random.randn(n)

bias = np.random.uniform(low=0.1, high=0.9)

inputs = []
for i in range(n):
    val = float(input(f"Enter your input: "))
    inputs.append(val)

z=0
for i in range(n):
    z += (inputs[i] * weights[i])

z = z + bias

binary_sigmoidal = 1 / (1 + np.exp(-z))
bipolar_sigmoidal = 2 / (1 + np.exp(-z)) - 1

print("Binary Sigmoidal = ", round(binary_sigmoidal, 3))
print("Bipolar Sigmoidal = ", round(bipolar_sigmoidal, 3))
