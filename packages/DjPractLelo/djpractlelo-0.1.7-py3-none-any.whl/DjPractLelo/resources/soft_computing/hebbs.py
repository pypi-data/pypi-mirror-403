# Initial values
w1 = 0.5   # old weight
w2 = -0.3  # old weight
b  = 0.2   # old bias

# Inputs
x1 = 1
x2 = 0
y  = 1     # target/output

# Update rule
w1_new = w1 + x1 * y
w2_new = w2 + x2 * y
b_new  = b + y

# Print results
print("Old w1:", w1, "-> New w1:", w1_new)
print("Old w2:", w2, "-> New w2:", w2_new)
print("Old b :", b,  "-> New b :", b_new)
