import csv

def csv_to_horus(filename, delimiter=','):
    try:
        with open(filename, mode='r') as file:
            reader = csv.DictReader(file, delimiter=delimiter)
            for row in reader:
                for field, value in row.items():
                    print(f"{field}: {value}")
    except FileNotFoundError:
        print("Error: File not found.")
    except Exception as e:
        print("An error occurred:", str(e))
csv_to_horus('color_srgb.csv')
