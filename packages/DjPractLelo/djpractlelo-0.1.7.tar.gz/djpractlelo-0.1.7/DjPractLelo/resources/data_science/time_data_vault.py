import pandas as pd
from datetime import datetime
import uuid

pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)

# ----------------------------------
# STEP 1: Generate Unique Time ID
# ----------------------------------
time_id = str(uuid.uuid4())

# ----------------------------------
# STEP 2: Create Time Hub
# ----------------------------------
time_hub = pd.DataFrame({
    "Time_ID": [time_id]
})

print("----- TIME HUB -----")
print(time_hub)

# ----------------------------------
# STEP 3: Capture Current Time
# ----------------------------------
current_time = datetime.now()

# ----------------------------------
# STEP 4: Create Time Satellite
# ----------------------------------
time_satellite = pd.DataFrame({
    "Time_ID": [time_id],
    "Date": [current_time.strftime("%Y-%m-%d")],
    "Time": [current_time.strftime("%H:%M:%S")],
    "Day": [current_time.strftime("%A")],
    "Month": [current_time.strftime("%B")],
    "Year": [current_time.year]
})

print("\n----- TIME SATELLITE -----")
print(time_satellite)

# ----------------------------------
# STEP 5: Create Time Link
# ----------------------------------
time_link = pd.DataFrame({
    "Link_ID": [str(uuid.uuid4())],
    "Time_ID": [time_id],
    "Event_Type": ["User Login"],
    "System": ["Application Server"]
})

print("\n----- TIME LINK -----")
print(time_link)
