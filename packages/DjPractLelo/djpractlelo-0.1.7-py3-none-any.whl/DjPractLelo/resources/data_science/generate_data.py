import pandas as pd
import random

# ----------------------------------
# STEP 1: Define Number of Records
# ----------------------------------
record_count = 12

# ----------------------------------
# STEP 2: Define Attribute Pools
# ----------------------------------
names = ["Amit", "Neha", "Ravi", "Pooja", "Ankit", "Kiran"]
departments = ["IT", "HR", "Finance", "Sales"]

# ----------------------------------
# STEP 3: Initialize Data Structure
# ----------------------------------
data = {
    "Emp_ID": [],
    "Emp_Name": [],
    "Department": [],
    "Age": [],
    "Monthly_Salary": []
}

# ----------------------------------
# STEP 4: Generate Data Records
# ----------------------------------
for i in range(record_count):
    data["Emp_ID"].append(1001 + i)
    data["Emp_Name"].append(random.choice(names))
    data["Department"].append(random.choice(departments))
    data["Age"].append(random.randint(22, 45))
    data["Monthly_Salary"].append(random.randint(25000, 60000))

# ----------------------------------
# STEP 5: Create DataFrame
# ----------------------------------
df = pd.DataFrame(data)

print("----- GENERATED DATA -----")
print(df)

# ----------------------------------
# STEP 6: Store Data in CSV
# ----------------------------------
df.to_csv("employee_generated_data.csv", index=False)

print("\nData successfully generated and stored in CSV file")
