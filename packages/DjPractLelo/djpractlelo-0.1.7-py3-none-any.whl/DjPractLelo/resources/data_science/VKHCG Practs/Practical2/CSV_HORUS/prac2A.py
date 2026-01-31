
print("Text delimited CSV to HORUS format.")
import pandas as pd

inputfile="countries.csv"
myfile= pd.read_csv(inputfile,encoding="latin-1")

print(myfile)

Pdata=myfile

# Remove columns 
Pdata.drop('alpha3',axis=1,inplace=True)

#Rename column name
Pdata.rename(columns={'name':'CountryName'},inplace=True)

# Sort data by CountryName
Pdata.sort_values('CountryName',axis=0,ascending=True,inplace=True)
print("Sorted Data Is")
print(Pdata)

Output=Pdata
OutputFile ="CSV_horus.csv"
Output.to_csv(OutputFile,index = False)
print('CSV to HORUS - Done')


