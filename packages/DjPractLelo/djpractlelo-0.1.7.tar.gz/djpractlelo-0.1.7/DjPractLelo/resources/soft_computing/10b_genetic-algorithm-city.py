import random, math

class City:
    def __init__(self, x, y):
        self.x, self.y = x, y
    def distance(self, city):
        return math.sqrt((self.x - city.x)**2 + (self.y - city.y)**2)
    def __repr__(self):
        return f"({self.x},{self.y})"

class Fitness:
    def __init__(self, route):
        self.route = route
    def distance(self):
        total = 0
        for i in range(len(self.route)):
            total += self.route[i].distance(self.route[(i+1)%len(self.route)])
        return total
    def fitness(self):
        return 1 / self.distance()

cities = [City(random.randint(0,50), random.randint(0,50)) for _ in range(5)]

population = [random.sample(cities, len(cities)) for _ in range(4)]

for _ in range(5):
    population.sort(key=lambda r: Fitness(r).fitness(), reverse=True)
    parent1, parent2 = population[0], population[1]
    child = parent1[:2] + [c for c in parent2 if c not in parent1[:2]]

best = population[0]
print("Best Route:", best)
print("Distance:", Fitness(best).distance())
