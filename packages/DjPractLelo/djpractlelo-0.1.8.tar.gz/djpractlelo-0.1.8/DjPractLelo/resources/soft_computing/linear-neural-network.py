# Take inputs from user
x1 = float(input("Enter first input (x1): "))
x2 = float(input("Enter second input (x2): "))
b= float(input("Enter bias value : "))


# Weights (fixed)
w1 = 0.5
w2 = 1.0

# Linear Neural Network formula
y = w1*x1 + w2*x2 + b
print("The weights and biase are ",w1,w2,b)

print("Output:", y)
