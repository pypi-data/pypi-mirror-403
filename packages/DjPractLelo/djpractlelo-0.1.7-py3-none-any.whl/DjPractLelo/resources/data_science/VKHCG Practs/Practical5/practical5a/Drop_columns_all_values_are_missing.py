import pandas as pd
import os

# Input and Output file paths
input_file = "C:/VKHCG/01-Vermeulen/00-RawData/Country_Currency_edited.csv"
output_file = "C:/VKHCG/01-Vermeulen/02-Assess/01-EDS/02-Python/drop_columns_all_values_are_missing.csv"

# Create output folder if it does not exist
os.makedirs("C:/VKHCG/01-Vermeulen/02-Assess/01-EDS/02-Python", exist_ok=True)

# Read Excel file (CORRECT FUNCTION)
data = pd.read_csv(input_file)

# Drop columns where all values are missing
clean_data = data.dropna(axis=1, how='all')

# Save cleaned Excel file
clean_data.to_csv(output_file, index=False)

print("File processed successfully.")
