# ii) Access customers' location using network router location

import pandas as pd
import os

input_file = "C:/VKHCG/01-Vermeulen/02-Assess/01-EDS/02-Python/Assess-Network-Routing-Customer.csv"
output_dir = "C:/VKHCG/01-Vermeulen/02-Assess/01-EDS/02-Python"
output_file = output_dir + "/Assess-Network-Routing-Customer.gml"

# Create output directory if it does not exist
os.makedirs(output_dir, exist_ok=True)

# Load customer data
customer_data = pd.read_csv(input_file, encoding="latin-1", low_memory=False)

# Display loaded data (first 5 rows)
print("Columns Loaded:", customer_data.columns.values)
print(customer_data.head())

# Save the data in GML format (Graph Modeling Language)
customer_data.to_csv(output_file, index=False, encoding="latin-1")

print("Customer routing data processed and saved successfully.")
