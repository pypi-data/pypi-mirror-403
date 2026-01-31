import pandas as pd

# ----------------------------------
# STEP 1: Load CSV Data
# ----------------------------------
df = pd.read_csv("transform_data.csv")

print("----- ORIGINAL DATA -----")
print(df)

# ----------------------------------
# STEP 2: Handle Missing Values
# ----------------------------------
df["HoursWorked"].fillna(df["HoursWorked"].mean(), inplace=True)

# ----------------------------------
# STEP 3: Data Transformation
# ----------------------------------

# Calculate Salary
df["Salary"] = df["HoursWorked"] * df["RatePerHour"]

# Add Bonus (10% of Salary)
df["Bonus"] = df["Salary"] * 0.10

# Calculate Total Pay
df["TotalPay"] = df["Salary"] + df["Bonus"]

# Convert Names to Uppercase
df["Name"] = df["Name"].str.upper()

# Categorize Salary Level
df["SalaryCategory"] = df["Salary"].apply(
    lambda x: "High" if x >= 35000 else "Medium"
)

print("\n----- TRANSFORMED DATA -----")
print(df)
