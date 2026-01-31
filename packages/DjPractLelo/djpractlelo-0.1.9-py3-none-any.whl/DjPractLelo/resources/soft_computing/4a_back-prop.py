import numpy as np

# Activation function and derivative
sig = lambda x: 1/(1+np.exp(-x))
dsig = lambda x: x*(1-x)

# Number of inputs
n = int(input("Enter number of inputs: "))

# Initialize weights and bias
weights = np.random.randn(n)
bias = np.random.rand()

# User input
inputs = np.array([float(input(f"Enter input {i+1}: ")) for i in range(n)])
target = float(input("Enter target output: "))

# Training
lr = 0.1
for _ in range(1000):
    out = sig(np.dot(inputs, weights) + bias)
    error = target - out
    delta = error * dsig(out)
    weights += lr * delta * inputs
    bias += lr * delta

# Output
out = sig(np.dot(inputs, weights) + bias)
print("Trained output:", out)
print("Trained weights:", weights)
print("Trained bias:", bias)
