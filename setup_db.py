#Skript, et luua andmebaas ja tabel questions
#Kasutatud allikas koodi kirjutamiseks: https://www.sqlitetutorial.net/sqlite-python/creating-tables/

import sqlite3

#Loo andmebaas nimega "questions.db"
conn = sqlite3.connect("questions.db")
cursor = conn.cursor()

#Loo esimene tabel
cursor.execute("""
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    row INTEGER NOT NULL,
    col INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL
)
""")

conn.commit()
conn.close()

