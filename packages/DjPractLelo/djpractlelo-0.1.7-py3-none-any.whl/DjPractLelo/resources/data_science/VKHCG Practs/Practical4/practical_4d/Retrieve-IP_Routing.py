import os
import pandas as pd
from math import radians, sin, cos, asin, sqrt

def haversine(lon1, lat1, lon2, lat2, km=True):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    a = sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2
    r = 6371 if km else 3956
    return round(2*asin(sqrt(a))*r, 3)


df = pd.read_csv(
   'C:/VKHCG/01-Vermeulen/00-RawData/IP_DATA_CORE.csv',
    usecols=['Country', 'Place Name', 'Latitude', 'Longitude'],
    encoding='latin-1'
)

os.makedirs('C:/VKHCG/01-Vermeulen/01-Retrieve/01-EDS/02-Python', exist_ok=True)

df = df.drop_duplicates().rename(columns={'Place Name': 'Place_Name'})
df['K'] = 1

cross = df.merge(df, on='K').drop('K', axis=1)

cross['DistanceKM'] = cross.apply(
    lambda r: haversine(r.Longitude_x, r.Latitude_x, r.Longitude_y, r.Latitude_y),
    axis=1
)

cross['DistanceMiles'] = cross.apply(
    lambda r: haversine(r.Longitude_x, r.Latitude_x, r.Longitude_y, r.Latitude_y, False),
    axis=1
)

cross.to_csv(
    'C:/VKHCG/01-Vermeulen/01-Retrieve/01-EDS/02-Python/Retrieve_IP_Routing.csv',
    index=False,
    encoding='latin-1'
)

print('Done')
