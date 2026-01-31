import pandas as pd

df = pd.read_csv("balance_sheet.csv")
print("Original Data")
print(df)

valid = df[df["Amount"] > 0]

print("\nValid Balance Sheet Data")
print(valid)
