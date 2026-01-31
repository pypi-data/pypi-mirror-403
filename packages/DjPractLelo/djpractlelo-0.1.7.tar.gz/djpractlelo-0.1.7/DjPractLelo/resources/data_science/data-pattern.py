import csv

data = []

with open("data-pattern.csv") as f:
    reader = csv.DictReader(f)
    for r in reader:
        data.append(r)

print("\n----- ORIGINAL DATA -----")
for r in data:
    print(r)

print("\n----- Students in IT Department -----")
for r in data:
    if r["Department"] == "IT":
        print(r)

print("\n----- Students Whose Names Start with 'A' -----")
for r in data:
    if r["Name"].startswith("A"):
        print(r)
