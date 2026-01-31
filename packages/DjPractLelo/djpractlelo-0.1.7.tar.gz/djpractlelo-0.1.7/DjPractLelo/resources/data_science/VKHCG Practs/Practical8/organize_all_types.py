import sqlite3 as sq
import pandas as pd

# Database connection
conn = sq.connect("sample_dw.db")

#Horizontal Organization
# Select specific rows based on conditions (all columns)
horizontal_df = pd.read_sql("SELECT * FROM Dim_BMI WHERE Indicator = 1 AND Age BETWEEN 20 AND 40 AND BMI >= 23;", conn)
print("\nHORIZONTAL ORGANIZATION")
print(horizontal_df)

#Vertical Organization
# Select specific columns (attributes) for all rows
vertical_df = pd.read_sql("SELECT PersonID, Age, BMI, Category FROM Dim_BMI;", conn)
print("\nVERTICAL ORGANIZATION")
print(vertical_df)

#Island-Style Organization
# Select specific rows and columns using multiple conditions
island_df = pd.read_sql("SELECT PersonID, Gender, Age, BMI, Category, City FROM Dim_BMI WHERE Indicator = 1 AND Age BETWEEN 20 AND 40 AND BMI >= 23 AND City <> 'Delhi' ORDER BY BMI DESC;", conn)
print("\nISLAND STYLE ORGANIZATION")
print(island_df)

#Secure Vault Organization
# Restrict and mask sensitive attributes for secure access
secure_vault_df = pd.read_sql("SELECT PersonID, Age, BMI, Category, Indicator, 'REDACTED' AS City FROM Dim_BMI WHERE Indicator = 1;", conn)
print("\nSECURE VAULT ORGANIZATION")
print(secure_vault_df)

# Close database connection
conn.close()
