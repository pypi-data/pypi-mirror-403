#membership function
def fuzzy(x, a=4, b=7, c=10):
    if x <= a or x >= c:
        return 0
    elif x <= b:
        return (x - a) / (b - a)
    else:
        return (c - x) / (c - b)

n = int(input("Enter number of shops: "))
ratings = []

# User input
for i in range(n):
    ratings.append(float(input(f"Enter rating for Shop {i+1}: ")))

# Fuzzification
memberships = [fuzzy(r) for r in ratings]
total = sum(memberships)

# Fuzzy ratios
print("\nShop  Membership  Fuzzy Ratio")
for i in range(n):
    ratio = memberships[i] / total if total != 0 else 0
    print(f"{i+1:>3}    {memberships[i]:.2f}        {ratio:.2f}")
