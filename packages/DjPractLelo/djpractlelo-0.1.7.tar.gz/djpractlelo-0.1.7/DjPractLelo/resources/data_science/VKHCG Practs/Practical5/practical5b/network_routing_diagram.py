# Merge Country, Company, and Customer data

import pandas as pd
import os

# Disable chained assignment warning
pd.options.mode.chained_assignment = None

# File paths (straight format)
country_file = "C:/VKHCG/01-Vermeulen/01-Retrieve/01-EDS/01-R/Retrieve_Country_Code.csv"
company_file = "C:/VKHCG/01-Vermeulen/01-Retrieve/01-EDS/02-Python/Retrieve_Router_Location.csv"
customer_file = "C:/VKHCG/01-Vermeulen/01-Retrieve/01-EDS/01-R/Retrieve_IP_DATA.csv"
output_dir = "C:/VKHCG/01-Vermeulen/02-Assess/01-EDS/02-Python"
output_file = output_dir + "/network_routing_output.csv"

# Create output folder
os.makedirs(output_dir, exist_ok=True)

# Load data files
country = pd.read_csv(country_file, encoding="latin-1",low_memory=False)
company = pd.read_csv(company_file, encoding="latin-1",low_memory=False)
customer = pd.read_csv(customer_file, encoding="latin-1",low_memory=False)

# Clean and rename country data
country = country.rename(columns={
    "Country": "Country_Name",
    "ISO-2-CODE": "Country_Code"
}).drop(columns=["ISO-M49", "ISO-3-Code", "RowID"])

# Clean and rename company data
company = company.rename(columns={"Country": "Country_Code"})

# Remove rows with missing values and rename customer column
customer = customer.dropna()
customer = customer.rename(columns={"Country": "Country_Code"})

# Merge company and country data
merged_data = pd.merge(company, country, on="Country_Code", how="inner")

# Add prefix 'Company_' to all column names
merged_data = merged_data.add_prefix("Company_")

# Save final data
merged_data.to_csv(output_file, index=False, encoding="latin-1")

print("Data merged and saved successfully.")
