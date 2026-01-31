# Drop columns where any value is missing

import pandas as pd
import os

# Straight input and output paths
input_file = "C:/VKHCG/01-Vermeulen/00-RawData/Country_Currency_edited.csv"
output_dir = "C:/VKHCG/01-Vermeulen/02-Assess/01-EDS/02-Python"
output_file = "C:/VKHCG/01-Vermeulen/02-Assess/01-EDS/02-Python/drop_columns_any_value_is_missing.csv"

# Create output directory if it does not exist
os.makedirs(output_dir, exist_ok=True)

# Load data
data = pd.read_csv(input_file)

# Drop columns having any missing values
clean_data = data.dropna(axis=1, how='any')

# Save cleaned file
clean_data.to_csv(output_file, index=False)

print("Columns with any missing values removed.")
