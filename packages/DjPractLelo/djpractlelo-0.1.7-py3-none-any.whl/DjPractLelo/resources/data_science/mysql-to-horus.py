import mysql.connector

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "mscit"
}

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()
query = "SELECT name, contactNo, address FROM users"
cursor.execute(query)

rows = cursor.fetchall()

print("NAME| CONTACTNO| ADDRESS")

for row in rows:
    name, contact, address = row
    print(f"{name}| {contact}| {address}")
cursor.close()
conn.close()
