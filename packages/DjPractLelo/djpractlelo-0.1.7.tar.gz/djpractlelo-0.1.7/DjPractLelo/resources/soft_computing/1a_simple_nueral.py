import numpy as np
import random

def activate_function(x):
    return 1 / (1 + np.exp(-x))

    
n=int(input("Enter Number of inputs you want:"))

weights = np.random.randn(n)

bias = np.random.uniform(low=0.1, high=0.9)

#User input
inputs = []
for i in range(number):
    val = float(input(f"Enter your input: "))
    inputs.append(val)

z=0
for i in range(n):
    z += (inputs[i] * weights[i])

z = z + bias

# Apply activation function
print(activate_function(z))







