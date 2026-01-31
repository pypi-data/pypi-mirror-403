import pandas as pd

# ----------------------------------
# STEP 1: Load CSV File
# ----------------------------------
df = pd.read_csv("organizing_data.csv")

print("----- ORIGINAL DATA -----")
print(df)

# ----------------------------------
# STEP 2: Sort Data by Price
# ----------------------------------
sorted_data = df.sort_values(by="Price", ascending=False)

print("\n----- SORTED BY PRICE (HIGH TO LOW) -----")
print(sorted_data)

# ----------------------------------
# STEP 3: Group Data by City
# ----------------------------------
city_group = df.groupby("City")["Quantity"].sum()

print("\n----- TOTAL QUANTITY SOLD PER CITY -----")
print(city_group)

# ----------------------------------
# STEP 4: Group Data by Product
# ----------------------------------
product_group = df.groupby("Product")["Quantity"].sum()

print("\n----- TOTAL QUANTITY SOLD PER PRODUCT -----")
print(product_group)
