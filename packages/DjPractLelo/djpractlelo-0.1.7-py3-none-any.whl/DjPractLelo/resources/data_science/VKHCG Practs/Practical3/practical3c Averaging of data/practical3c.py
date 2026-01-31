import pandas as pd
OutputFile='Retrieve_Router_Location.csv'

sFileName='C:/msc_dataset/Practical_3c/IP_DATA_CORE.csv'

IP_DATA_ALL=pd.read_csv(sFileName,header=0,low_memory=False,usecols=['Country','Place Name','Latitude','Longitude'], encoding="latin-1")
IP_DATA_ALL.rename(columns={'Place Name': 'Place_Name'}, inplace=True)

AllData=IP_DATA_ALL[['Country', 'Place_Name','Latitude']]
print(AllData)

MeanData=AllData.groupby(['Country', 'Place_Name'])['Latitude'].mean()
print(MeanData)       
