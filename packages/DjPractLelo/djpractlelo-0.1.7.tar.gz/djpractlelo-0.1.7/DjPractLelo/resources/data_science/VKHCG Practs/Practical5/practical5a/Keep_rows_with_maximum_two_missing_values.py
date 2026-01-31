# Remove rows with maximum two missing values

import pandas as pd
import os

# Straight input and output paths
input_file = "C:/VKHCG/01-Vermeulen/00-RawData/Country_Currency_edited.csv"
output_dir = "C:/VKHCG/01-Vermeulen/02-Assess/01-EDS/02-Python"
output_file = "C:/VKHCG/01-Vermeulen/02-Assess/01-EDS/02-Python/keep_rows_with_maximum_two_missing_values.csv.csv"

# Create output directory if it does not exist
os.makedirs(output_dir, exist_ok=True)

# Load data
data = pd.read_csv(input_file)

# Keep rows having at least (total columns - 2) non-missing values
clean_data = data.dropna(thresh=len(data.columns) - 2)

# Save cleaned data
clean_data.to_csv(output_file, index=False)

print("Rows with more than two missing values removed.")
