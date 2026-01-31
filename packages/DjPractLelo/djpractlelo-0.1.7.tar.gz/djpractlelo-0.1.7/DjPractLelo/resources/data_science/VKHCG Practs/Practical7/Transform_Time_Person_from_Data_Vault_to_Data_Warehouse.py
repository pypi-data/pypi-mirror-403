import os
import uuid
import pandas as pd
import sqlite3 as sq
from datetime import datetime
from pytz import timezone

COMPANY = '01-Vermeulen'

# Database paths
DV_DB = 'C:/VKHCG/88-DV/datavault.db'
DW_DB = 'C:/VKHCG/99-DW/datawarehouse.db'

# Ensure DW directory exists
os.makedirs('C:/VKHCG/99-DW', exist_ok=True)

# Database connections
conn_dv = sq.connect(DV_DB)
conn_dw = sq.connect(DW_DB)

# TIME TRANSFORMATION
# Birth time in UTC
birth_utc = datetime(1960, 12, 20, 10, 15, 0, tzinfo=timezone('UTC'))
birth_zone = 'Atlantic/Reykjavik'

# Convert UTC to local zone
birth_local = birth_utc.astimezone(timezone(birth_zone))

# Generate keys
time_id = str(uuid.uuid4())
datetime_key = birth_utc.strftime("%Y-%m-%d-%H-%M-%S")

# Time Hub record
time_hub = pd.DataFrame([{
    "TimeID": time_id,
    "ZoneBaseKey": "UTC",
    "DateTimeKey": datetime_key,
    "DateTimeValue": birth_utc.strftime("%Y-%m-%d %H:%M:%S")
}]).set_index("TimeID")

# Store Time Hub
time_hub.to_sql("Hub-Time-Gunnarsson", conn_dv, if_exists="replace")
time_hub.to_sql("Dim-Time-Gunnarsson", conn_dw, if_exists="replace")

# Time Satellite record
time_sat = pd.DataFrame([{
    "TimeID": time_id,
    "Zone": birth_zone,
    "DateTimeValue": birth_local.strftime("%Y-%m-%d %H:%M:%S")
}]).set_index("TimeID")

zone_fix = birth_zone.replace('/', '-')

# Store Time Satellite
time_sat.to_sql(f"Satellite-Time-{zone_fix}-Gunnarsson", conn_dv, if_exists="replace")
time_sat.to_sql(f"Dim-Time-{zone_fix}-Gunnarsson", conn_dw, if_exists="replace")

# PERSON TRANSFORMATION
first_name = "Guðmundur"
last_name = "Gunnarsson"

person_id = str(uuid.uuid4())

# Person Hub / Dimension record
person = pd.DataFrame([{
    "PersonID": person_id,
    "FirstName": first_name,
    "LastName": last_name,
    "BirthDateUTC": birth_utc.strftime("%Y-%m-%d %H:%M:%S")
}]).set_index("PersonID")

# Store Person Hub and Dimension
person.to_sql("Hub-Person-Gunnarsson", conn_dv, if_exists="replace")
person.to_sql("Dim-Person-Gunnarsson", conn_dw, if_exists="replace")

# Cleanup
conn_dv.close()
conn_dw.close()

print("Transform step completed successfully.")
