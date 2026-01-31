import os
import sys
import uuid
import pandas as pd
import sqlite3 as sq
from datetime import datetime
from pytz import timezone


# Base Configuration
COMPANY = '01-Vermeulen'

# Transform database
TRANSFORM_DB ='C:/VKHCG/04-Transform/SQLite/Vermeulen.db'
os.makedirs(os.path.dirname(TRANSFORM_DB), exist_ok=True)

# Data Warehouse database
DW_DB ='C:/VKHCG/99-DW/datawarehouse.db'
os.makedirs('C:/VKHCG/99-DW', exist_ok=True)

# Database connections
conn_transform = sq.connect(TRANSFORM_DB)
conn_dw = sq.connect(DW_DB)

# DIMENSION : TIME

birth_zone = 'Atlantic/Reykjavik'
birth_utc = datetime(1960, 12, 20, 10, 15, 0, tzinfo=timezone('UTC'))
birth_local = birth_utc.astimezone(timezone(birth_zone))

time_id = str(uuid.uuid4())

dim_time = pd.DataFrame([{
    "TimeID": time_id,
    "UTCDate": birth_utc.strftime("%Y-%m-%d %H:%M:%S"),
    "LocalTime": birth_local.strftime("%Y-%m-%d %H:%M:%S"),
    "TimeZone": birth_zone
}]).set_index("TimeID")

dim_time.to_sql("Dim-Time", conn_transform, if_exists="replace")
dim_time.to_sql("Dim-Time", conn_dw, if_exists="replace")

# DIMENSION : PERSON
person_id = str(uuid.uuid4())

dim_person = pd.DataFrame([{
    "PersonID": person_id,
    "FirstName": "Guðmundur",
    "LastName": "Gunnarsson",
    "BirthDateUTC": birth_utc.strftime("%Y-%m-%d %H:%M:%S")
}]).set_index("PersonID")

dim_person.to_sql("Dim-Person", conn_transform, if_exists="replace")
dim_person.to_sql("Dim-Person", conn_dw, if_exists="replace")

# FACT : PERSON BORN AT TIME
fact_id = str(uuid.uuid4())

fact_person_time = pd.DataFrame([{
    "FactID": fact_id,
    "PersonID": person_id,
    "TimeID": time_id
}]).set_index("FactID")

fact_person_time.to_sql("Fact-Person-Born-At-Time", conn_transform, if_exists="replace")
fact_person_time.to_sql("Fact-Person-Born-At-Time", conn_dw, if_exists="replace")

# Cleanup
conn_transform.close()
conn_dw.close()

print("Sun model transformation completed successfully.")



#result prinitng
conn = sq.connect("C:/VKHCG/99-DW/datawarehouse.db")

print("Tables in Data Warehouse:")
tables = pd.read_sql_query(
    "SELECT name FROM sqlite_master WHERE type='table';",
    conn
)
print(tables)

print("\nDim-Time:")
print(pd.read_sql_query("SELECT * FROM [Dim-Time];", conn))

print("\nDim-Person:")
print(pd.read_sql_query("SELECT * FROM [Dim-Person];", conn))

print("\nFact-Person-Born-At-Time:")
print(pd.read_sql_query("SELECT * FROM [Fact-Person-Born-At-Time];", conn))

conn.close()

