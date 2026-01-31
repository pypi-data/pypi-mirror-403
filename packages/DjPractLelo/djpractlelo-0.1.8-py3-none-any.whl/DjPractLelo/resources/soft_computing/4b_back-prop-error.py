import numpy as np

# Sigmoid and derivative
sig = lambda x: 1/(1+np.exp(-x))
dsig = lambda x: x*(1-x)

# Number of inputs
n = int(input("Enter number of inputs: "))

# User inputs
inputs = np.array([float(input(f"Enter input {i+1}: ")) for i in range(n)])
target = float(input("Enter target output: "))

# Initialize weights and bias
weights = np.random.randn(n)
bias = np.random.rand()

# Learning rate and epochs
lr = 0.1
epochs = 1000

# Training loop (backpropagation)
for _ in range(epochs):
    out = sig(np.dot(inputs, weights) + bias)  # Forward pass
    error = target - out
    delta = error * dsig(out)
    weights += lr * delta * inputs            # Update weights
    bias += lr * delta                         # Update bias

# Final output
out = sig(np.dot(inputs, weights) + bias)
print("Trained output:", out)
print("Trained weights:", weights)
print("Trained bias:", bias)
