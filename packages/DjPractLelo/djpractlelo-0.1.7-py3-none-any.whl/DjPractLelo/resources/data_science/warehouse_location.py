import pandas as pd

data = {
    "City": ["A", "B", "C", "D", "E", "F", "G", "H"],
    "Demand": [200, 500, 300, 450, 600, 250, 700, 350]
}

df = pd.DataFrame(data)
print(df)

best = df.loc[df["Demand"].idxmax()]

print("\nBest Warehouse Location")
print(best)
