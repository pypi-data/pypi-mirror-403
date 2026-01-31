import sys
import os
import pandas as pd

Base = ''

# Input file
sFileName = 'C:/VKHCG/01-Vermeulen/00-RawData/IP_DATA_ALL.csv'
print('Loading :', sFileName)

IP_DATA_ALL = pd.read_csv(
    sFileName,
    header=0,
    low_memory=False,
    encoding="latin-1"
)

# Output directory
sFileDir = Base + '/01-Vermeulen/01-Retrieve/01-EDS/02-Python'
os.makedirs(sFileDir, exist_ok=True)

# Basic info
print('Rows:', IP_DATA_ALL.shape[0])
print('Columns:', IP_DATA_ALL.shape[1])

# Fix column names
IP_DATA_ALL.columns = [
    col.strip().replace(' ', '.')
    for col in IP_DATA_ALL.columns
]

# Add RowID
IP_DATA_ALL.index.name = 'RowID'

# Save output
sFileName2 = sFileDir + '/Retrieve_IP_DATA.csv'
IP_DATA_ALL.to_csv(sFileName2, index=True, encoding="latin-1")

print('### Done!! ############################################')
