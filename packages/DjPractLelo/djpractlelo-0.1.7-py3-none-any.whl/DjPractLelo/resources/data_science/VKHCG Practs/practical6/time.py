import os, uuid, sqlite3 as sq, pandas as pd
from datetime import datetime, timedelta
from pytz import timezone, all_timezones

print("Starting program")

os.makedirs("C:/VKHCG", exist_ok=True)
con = sq.connect("C:/VKHCG/time.db")
print("Database opened")

print("Generating UTC time data")
df = pd.DataFrame([
    [str(uuid.uuid4()),
     (datetime(2018,1,1)-timedelta(h)).strftime("%Y-%m-%d-%H"),
     (datetime(2018,1,1)-timedelta(h)).replace(tzinfo=timezone("UTC"))]
    for h in range(24)
], columns=["ID","Key","UTC"]).set_index("ID")

print("Storing Hub-Time table")
df[["Key"]].to_sql("Hub-Time", con, if_exists="replace")

print("Creating timezone tables")
for z in all_timezones:
    pd.DataFrame({
        "ID":[str(uuid.uuid4()) for _ in df.index],
        "Key":df["Key"],
        "Time":df["UTC"].apply(lambda x: x.astimezone(timezone(z)).strftime("%Y-%m-%d %H"))
    }).set_index("ID").to_sql(f"Time-{z.replace('/','-')}", con, if_exists="replace")

print("Showing tables in database")
print(pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", con))

print("Showing Hub-Time data")
print(pd.read_sql("SELECT * FROM 'Hub-Time' LIMIT 5", con))

con.execute("VACUUM;")
con.close()

