import os, sys, uuid, pandas as pd, sqlite3 as sq
from datetime import datetime
from pytz import timezone

# Paths
TRANSFORM_DB = 'C:/VKHCG/04-Transform/SQLite/Vermeulen.db'
DV_DB = 'C:/VKHCG/88-DV/datavault.db'
DW_DB = 'C:/VKHCG/99-DW/datawarehouse.db'

os.makedirs(os.path.dirname(TRANSFORM_DB), exist_ok=True)
os.makedirs(os.path.dirname(DW_DB), exist_ok=True)
os.makedirs(os.path.dirname(DV_DB), exist_ok=True)

# Connections
conn_transform = sq.connect(TRANSFORM_DB)
conn_dw = sq.connect(DW_DB)
conn_dv = sq.connect(DV_DB)

#Create Data Vault tables if missing 
conn_dv.execute("""
CREATE TABLE IF NOT EXISTS [Hub-Time] (
    DateTimeValue TEXT
);
""")
conn_dv.execute("""
CREATE TABLE IF NOT EXISTS [Hub-Person] (
    FirstName TEXT,
    SecondName TEXT,
    LastName TEXT,
    BirthDateKey TEXT
);
""")

# Insert sample data if tables are empty
if conn_dv.execute("SELECT COUNT(*) FROM [Hub-Time];").fetchone()[0] == 0:
    conn_dv.execute("INSERT INTO [Hub-Time] VALUES ('1960-12-20 10:15:00');")
if conn_dv.execute("SELECT COUNT(*) FROM [Hub-Person];").fetchone()[0] == 0:
    conn_dv.execute("INSERT INTO [Hub-Person] VALUES ('Guðmundur','','Gunnarsson','1960-12-20 10:15:00');")
conn_dv.commit()

#Build Time Dimension 
time_raw = pd.read_sql_query("SELECT DateTimeValue FROM [Hub-Time];", conn_dv)
zones = ['Atlantic/Reykjavik', 'Europe/London', 'UTC']
time_rows = []
for _, row in time_raw.iterrows():
    utc_time = datetime.strptime(row["DateTimeValue"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone("UTC"))
    for z in zones:
        time_rows.append({
            "TimeID": str(uuid.uuid4()),
            "UTCDate": utc_time.strftime("%Y-%m-%d %H:%M:%S"),
            "LocalTime": utc_time.astimezone(timezone(z)).strftime("%Y-%m-%d %H:%M:%S"),
            "TimeZone": z
        })
dim_time = pd.DataFrame(time_rows).set_index("TimeID")
dim_time.to_sql("Dim-Time", conn_transform, if_exists="replace")
dim_time.to_sql("Dim-Time", conn_dw, if_exists="replace")

# Build Person Dimension 
person_raw = pd.read_sql_query("SELECT * FROM [Hub-Person];", conn_dv)
person_rows = []
for _, row in person_raw.iterrows():
    person_rows.append({
        "PersonID": str(uuid.uuid4()),
        "FirstName": row["FirstName"],
        "SecondName": row["SecondName"] if pd.notna(row["SecondName"]) else "",
        "LastName": row["LastName"],
        "Zone": "UTC",
        "BirthDate": row["BirthDateKey"]
    })
dim_person = pd.DataFrame(person_rows).set_index("PersonID")
dim_person.to_sql("Dim-Person", conn_transform, if_exists="replace")
dim_person.to_sql("Dim-Person", conn_dw, if_exists="replace")

# Close connections
conn_transform.close()
conn_dw.close()
conn_dv.close()

print("Data Warehouse dimensions built successfully.")
