import csv

total = 0
count = 0
data = []

with open("average.csv") as f:
    reader = csv.DictReader(f)
    for r in reader:
        data.append(r)
        if r["Salary"] != "":
            total += int(r["Salary"])
            count += 1

print("\n----- ORIGINAL DATA -----")
for r in data:
    print(r)

average = total / count

print("\nAverage Salary:", average)
