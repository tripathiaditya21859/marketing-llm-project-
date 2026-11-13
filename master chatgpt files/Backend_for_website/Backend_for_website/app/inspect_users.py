import sqlite3
from app.config import DATABASE_PATH

conn = sqlite3.connect(str(DATABASE_PATH))
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()

print("USER TABLE COLUMNS:")
for column in columns:
    print(column)

cursor.execute("SELECT * FROM users")
users = cursor.fetchall()

print("\nEXISTING USERS:")
for user in users:
    print(user)

conn.close()


