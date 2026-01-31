import pandas as pd
from datetime import datetime

csv_file = "data.csv"

def log(level, message):
    print(f"{datetime.now()} | {level} | {message}")

try:
    df = pd.read_csv(csv_file)
    log("INFO", f"{csv_file} loaded successfully")

    if df.isnull().values.any():
        log("WARNING", "Null values detected in CSV file")
    else:
        log("INFO", "No null values found")

except FileNotFoundError:
    log("ERROR", f"{csv_file} not found")

except Exception as e:
    log("ERROR", str(e))
