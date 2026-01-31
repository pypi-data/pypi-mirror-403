import sqlite3 as sq

conn = sq.connect("sample_dw.db")
cur = conn.cursor()

cur.execute("""
DROP TABLE IF EXISTS Dim_BMI;
""")

cur.execute("""
CREATE TABLE Dim_BMI (
    PersonID INTEGER PRIMARY KEY,
    Gender TEXT,
    Age INTEGER,
    Height REAL,
    Weight REAL,
    BMI REAL,
    Category TEXT,
    Indicator INTEGER,
    City TEXT
);
""")

data = [
    (1, 'M', 22, 1.72, 70, 23.7, 'Normal', 1, 'Mumbai'),
    (2, 'F', 19, 1.60, 48, 18.8, 'Normal', 1, 'Delhi'),
    (3, 'M', 45, 1.75, 92, 30.0, 'Obese', 0, 'Pune'),
    (4, 'F', 34, 1.55, 50, 20.8, 'Normal', 1, 'Chennai'),
    (5, 'M', 28, 1.80, 85, 26.2, 'Overweight', 1, 'Mumbai'),
    (6, 'F', 52, 1.58, 72, 28.8, 'Overweight', 0, 'Delhi'),
    (7, 'M', 41, 1.68, 78, 27.6, 'Overweight', 1, 'Bangalore'),
    (8, 'F', 24, 1.62, 44, 16.8, 'Underweight', 1, 'Pune'),
    (9, 'M', 36, 1.70, 68, 23.5, 'Normal', 1, 'Chennai'),
    (10, 'F', 29, 1.65, 90, 33.1, 'Obese', 0, 'Mumbai'),
    (11, 'M', 55, 1.73, 74, 24.7, 'Normal', 1, 'Delhi'),
    (12, 'F', 47, 1.59, 62, 24.5, 'Normal', 1, 'Bangalore'),
    (13, 'M', 33, 1.82, 110, 33.2, 'Obese', 0, 'Pune'),
    (14, 'F', 21, 1.68, 58, 20.5, 'Normal', 1, 'Mumbai'),
    (15, 'M', 26, 1.76, 65, 21.0, 'Normal', 1, 'Chennai')
]

cur.executemany("""
INSERT INTO Dim_BMI VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
""", data)

cur.execute("SELECT * FROM Dim_BMI;")
rows = cur.fetchall()

for row in rows:
    print(row)

conn.commit()
conn.close()
