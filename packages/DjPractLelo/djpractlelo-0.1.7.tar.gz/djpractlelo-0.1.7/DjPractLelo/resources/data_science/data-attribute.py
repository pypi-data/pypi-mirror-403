import pandas as pd
data = pd.read_csv("attributes.csv")

print("\n----- Students with Marks >= 80 -----")
print(data[data["Marks"] >= 80])

print("\n----- Marks Statistics -----")
print("Maximum Marks:", data["Marks"].max())
print("Minimum Marks:", data["Marks"].min())

print("\n----- Department-wise Student Count -----")
print(data["Department"].value_counts())


