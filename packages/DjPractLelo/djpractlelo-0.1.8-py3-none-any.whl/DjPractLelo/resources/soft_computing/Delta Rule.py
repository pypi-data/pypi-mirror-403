# Initial values
w1 = 0.5   # old weight
w2 = -0.3  # old weight
b  = 0.2   # old bias

# Inputs
x1 = 1
x2 = 0

# Target and output
t = 1      # target output
y = 0      # actual output (predicted by neuron)

# Learning rate
eta = 0.1

# Error
error = t - y

# Delta rule update
w1_new = w1 + eta * error * x1
w2_new = w2 + eta * error * x2
b_new  = b  + eta * error

# Print results
print("Old w1:", w1, "-> New w1:", w1_new)
print("Old w2:", w2, "-> New w2:", w2_new)
print("Old b :", b,  "-> New b :", b_new)
