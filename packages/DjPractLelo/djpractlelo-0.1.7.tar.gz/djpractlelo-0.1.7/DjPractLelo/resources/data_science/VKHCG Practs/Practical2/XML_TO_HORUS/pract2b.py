#install pandas lxml
import pandas as pd

#Read XML
df = pd.read_xml("data.xml")

#Rename column to uppercase
df.columns = [col.upper() for col in df.columns]
print(df)

#Saving
df.to_csv("horus_output.csv", index=False)
print("Horus CSV created: horus_output.csv")
