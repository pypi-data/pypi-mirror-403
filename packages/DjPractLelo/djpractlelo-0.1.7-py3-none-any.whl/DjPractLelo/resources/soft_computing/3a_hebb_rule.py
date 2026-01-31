import numpy as np

# Sigmoid activation function
def activate_function(x):
    return 1 / (1 + np.exp(-x))

# Learning rate for Hebbian learning
learning_rate = 0.1

n = int(input("Enter number of inputs you want: "))

weights = np.random.randn(n)
bias = np.random.randn()

print("\nInitial weights:", weights)
print("Bias:", bias, "\n")

inputs = []
for i in range(n):
    val = float(input(f"Enter input {i+1}: "))
    inputs.append(val)

inputs = np.array(inputs)

y=0
for i in range(n):
    y += (inputs[i] * weights[i])

y = y + bias
print("\nWeighted sum (z) before Hebbian update:", y)

output = activate_function(y)
print("Output before Hebbian update:", round(output, 3))




#Hebbian Learning Rule
target = round(output)

# Update weights according to Hebb's rule
weights += learning_rate * inputs
bias += learning_rate   

print("\nWeights after Hebbian learning:", weights)
print("Bias after Hebbian learning:", bias)

#Compute new sum and output after learning
for i in range(n):
    y += (inputs[i] * weights[i])

y= y + bias
output_new = activate_function(y)

print("\nSum after Hebbian update:",y)
print("Output after Hebbian update:",output)
