import numpy as np

# Sigmoid activation function
def activate_function(x):
    return 1 / (1 + np.exp(-x))

# Learning rate
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

y = 0
for i in range(n):
    y += (inputs[i] * weights[i])

y = y + bias
print("\nWeighted sum (z) before learning:", y)

output = activate_function(y)
print("Output before learning:",output)






# -------- Delta Rule --------
target = float(input("Enter target output (0 or 1): "))

error = target - output
print(error)


# Update weights and bias using Delta rule
weights += learning_rate * inputs*error
bias += learning_rate

print("\nWeights after Delta learning:", weights)
print("Bias after Delta learning:", bias)

#New sum and output after learning
y = 0
for i in range(n):
    y += (inputs[i] * weights[i])

y = y + bias
output = activate_function(y)

print("\nSum after Delta update:", y)
print("Output after Delta update:", output)
