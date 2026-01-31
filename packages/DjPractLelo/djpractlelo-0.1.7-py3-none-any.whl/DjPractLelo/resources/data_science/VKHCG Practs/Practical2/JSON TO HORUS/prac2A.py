

print("Text delimited CSV to HORUS format.")
import pandas as pd

inputfile="countries.json"
myfile= pd.read_json(inputfile,encoding="latin-1")

print(myfile)


Pdata=myfile

# Remove columns 
Pdata.drop('alpha3',axis=1,inplace=True)
print(Pdata)

#Rename column name
Pdata.rename(columns={'name':'CountryName'},inplace=True)
print(Pdata)


# Set new Index
Pdata.set_index('CountryName',inplace=True)
print(Pdata)

# Sort data by CountryName
Pdata.sort_values('CountryName',axis=0,ascending=True,inplace=True)
print("Sorted Data Is")
print(Pdata)

Output=Pdata
OutputFile ="Json_horus.csv"
Output.to_csv(OutputFile,index = False)
print('CSV to HORUS - Done')


