import pandas as pd

data = {
    "Name": ["A", "B", "C", "D", "E", "F", "G"],
    "Hours": [160, 170, 150, 180, 165, 175, 155],
    "Rate": [200, 180, 220, 190, 210, 205, 195]
}

df = pd.DataFrame(data)
df["Salary"] = df["Hours"] * df["Rate"]

print(df)
