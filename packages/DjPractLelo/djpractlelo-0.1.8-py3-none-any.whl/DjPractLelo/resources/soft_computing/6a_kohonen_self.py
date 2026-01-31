import random
cities = [
    [0, 0],      # Kudal
    [-25, 0],    # Malvan
    [0, -18],    # Sawantwadi
    [0, 35],     # Kanakavali
    [0, 65],     # Vaibhavwadi
    [-35, 65],   # Devgad
    [-20, -18]   # Vengurle
]

city_names = ["Kudal", "Malvan", "Sawantwadi", "Kanakavali", "Vaibhavwadi", "Devgad", "Vengurle"]

neurons = 3          # number of clusters.
learning_rate = 0.3
epochs = 50

# Initialize neuron positions randomly
weights = [[random.uniform(-50, 70), random.uniform(-20, 70)] for _ in range(neurons)]

#Training
for _ in range(epochs):
    for city in cities:
        winner = min(range(neurons), key=lambda i: (city[0]-weights[i][0])**2 + (city[1]-weights[i][1])**2)
        for j in range(2):
            weights[winner][j] += learning_rate * (city[j] - weights[winner][j])

# Print cluster centers
print("Neuron positions (cluster centers):")
for i, w in enumerate(weights):
    print(f"Neuron {i}: {w}")

# Assign each city to its nearest neuron
print("\nCity assignments:")
for idx, city in enumerate(cities):
    nearest = min(range(neurons), key=lambda i: (city[0]-weights[i][0])**2 + (city[1]-weights[i][1])**2)
    print(f"{city_names[idx]} -> Cluster {nearest}")

