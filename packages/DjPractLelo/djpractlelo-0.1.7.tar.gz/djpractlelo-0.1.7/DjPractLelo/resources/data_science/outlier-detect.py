import csv

data = []
salaries = []

with open("outlier.csv") as f:
    reader = csv.DictReader(f)
    for r in reader:
        data.append(r)
        salaries.append(int(r["Salary"]))

# calculate mean
mean = sum(salaries) / len(salaries)

# threshold for outlier
threshold = mean * 1.5

print("\n----- ORIGINAL DATA -----")
for r in data:
    print(r)

print("\n----- OUTLIERS -----")
for r in data:
    if int(r["Salary"]) > threshold:
        print(r)
