import pandas as pd
import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='student'
)

query = "SELECT * FROM stud"
df = pd.read_sql(query, conn)

df.rename(columns={ 'fullname': 'name'}, inplace=True)

df.to_csv("horus_format_output.csv", index=False)

print("Sql_horus file saved")
conn.close()
