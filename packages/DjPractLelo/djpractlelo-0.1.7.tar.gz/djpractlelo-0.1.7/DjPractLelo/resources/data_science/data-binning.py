import csv

data = []

with open("binning.csv") as f:
    reader = csv.DictReader(f)
    data = list(reader)

print("\n----- ORIGINAL DATA -----")
for r in data:
    print(r)

for r in data:
    age = int(r["Age"])

    if age < 30:
        r["Age_Group"] = "Young"
    elif age <= 45:
        r["Age_Group"] = "Adult"
    else:
        r["Age_Group"] = "Senior"

print("\n----- DATA AFTER BINNING -----")
for r in data:
    print(r)
