import os
import pandas as pd

# Load the dataset
input_file = 'C:/msc_dataset/Practical_4c/IP_DATA_ALL.csv'
df = pd.read_csv(input_file, header=0, low_memory=False, encoding="latin-1")

# Create output folder if it doesn't exist
output_dir = 'C:/msc_dataset/Praqctical_4c/4c-Python'
os.makedirs(output_dir, exist_ok=True)

# Step 3: Show dataset dimensions
print('Rows:', df.shape[0])
print('Columns:', df.shape[1])

# Step 4: Show raw column names
print('Raw Data Set')
for col in df.columns:
    print(col, type(col))

# Step 5: Clean column names (replace spaces with dots)
df.columns = [col.strip().replace(" ", ".") for col in df.columns]

# Step 6: Show cleaned column names
print('Fixed Data Set')
for col in df.columns:
    print(col, type(col))

# Step 7: Set index name and export to CSV
df.index.name = 'RowID'
output_file = os.path.join(output_dir, 'Retrieve_IP_DATA.csv')
df.to_csv(output_file, index=True, encoding="latin-1")
