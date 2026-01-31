import csv

file_name = "fixer-uti.csv"
data = []
with open(file_name, 'r') as file:
    reader = csv.DictReader(file)
    headers = reader.fieldnames

    for row in reader:
        data.append(row)

print("\n----- ORIGINAL DATA -----")
for row in data:
    print(row)
for row in data:
    for col in headers:
        if row[col] == "":
            row[col] = "NA"
print("\n----- FIXED DATA (Missing Values Filled with NA) -----")
for row in data:
    print(row)
