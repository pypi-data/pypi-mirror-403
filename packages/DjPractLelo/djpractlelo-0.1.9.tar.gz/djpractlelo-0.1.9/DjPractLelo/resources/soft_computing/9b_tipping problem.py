def fuzzy(x, a, b, c):
    if x <= a or x >= c:
        return 0
    elif x <= b:
        return (x - a) / (b - a)
    else:
        return (c - x) / (c - b)

# ---- User Input ----
service = float(input("Enter service quality (0-10): "))
food = float(input("Enter food quality (0-10): "))

# ---- Fuzzification ----
service_poor = fuzzy(service, 0, 0, 5)
service_avg  = fuzzy(service, 3, 5, 7)
service_good = fuzzy(service, 5, 10, 10)

food_bad  = fuzzy(food, 0, 0, 5)
food_avg  = fuzzy(food, 3, 5, 7)
food_good = fuzzy(food, 5, 10, 10)

# ---- Rule Evaluation ----
low_tip    = max(service_poor, food_bad)
medium_tip = service_avg
high_tip   = min(service_good, food_good)

# ---- Defuzzification (Weighted Average) ----
tip = (low_tip*5 + medium_tip*15 + high_tip*25) / \
      (low_tip + medium_tip + high_tip)

print(f"\nRecommended Tip: {tip:.2f}%")
