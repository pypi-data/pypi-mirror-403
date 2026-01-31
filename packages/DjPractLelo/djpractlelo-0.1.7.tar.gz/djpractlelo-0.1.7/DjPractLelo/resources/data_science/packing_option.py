import pandas as pd

data = {
    "Option": ["BoxA", "BoxB", "BoxC", "BoxD", "BoxE", "BoxF", "BoxG"],
    "Cost": [120, 100, 150, 90, 110, 85, 130]
}

df = pd.DataFrame(data)
print(df)

best_index = df["Cost"].idxmin()
df.drop(best_index, inplace=True)

print("\nAfter Removing Best Option")
print(df)
