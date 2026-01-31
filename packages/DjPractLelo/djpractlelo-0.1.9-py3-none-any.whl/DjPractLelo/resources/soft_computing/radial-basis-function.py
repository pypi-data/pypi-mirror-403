import math

# Radial Basis Function (Gaussian)
def rbf(x, c, sigma):
    return math.exp(-((x - c)**2) / (2 * sigma**2))

# Hidden neurons centers
centers = [1, 2, 3]      # positions of RBF neurons
sigma = 1.0              # width of Gaussian

# Output weights
weights = [0.5, -1.0, 0.8]

# User input
x = float(input("Enter input value: "))

# Compute output
y = 0
for i in range(len(centers)):
    y += weights[i] * rbf(x, centers[i], sigma)

print("RBF Network Output:", y)
