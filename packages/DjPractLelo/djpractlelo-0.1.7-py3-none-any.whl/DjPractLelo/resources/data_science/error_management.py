import pandas as pd

# Load data
df = pd.read_csv("error_management.csv")
print("Original Data")
print(df)

# Fill missing values
df.fillna(0, inplace=True)

# Remove duplicate rows
df.drop_duplicates(inplace=True)

# Convert numeric column safely
df["Age"] = pd.to_numeric(df["Age"], errors="coerce")

print("\nCleaned Data")
print(df)
