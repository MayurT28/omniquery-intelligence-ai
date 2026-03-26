import mysql.connector
import sqlite3
from decimal import Decimal

# 1. Connect to your LOCAL MySQL
mysql_db = mysql.connector.connect(
    host="localhost", 
    user="root", 
    password="1234", # <--- Put your real password here
    database="sakila"
)
mysql_cursor = mysql_db.cursor()

# 2. Create the SQLITE file
sqlite_db = sqlite3.connect("sakila.db")
sqlite_cursor = sqlite_db.cursor()

# 3. Tables to copy
tables = ['film', 'actor', 'category', 'film_category', 'inventory']

for table in tables:
    print(f"📦 Copying table: {table}...")
    
    # Get Data
    mysql_cursor.execute(f"SELECT * FROM {table}")
    rows = mysql_cursor.fetchall()
    
    # --- 🛠️ ADVANCED CLEANING FOR SQLITE ---
    cleaned_rows = []
    for row in rows:
        new_row = []
        for item in row:
            if isinstance(item, Decimal):
                new_row.append(float(item)) # Convert Money to Float
            elif isinstance(item, set):
                new_row.append(", ".join(item)) # Convert {'Set'} to "String"
            else:
                new_row.append(item)
        cleaned_rows.append(tuple(new_row))
    
    # Get column names
    mysql_cursor.execute(f"SHOW COLUMNS FROM {table}")
    cols = [f"'{c[0]}'" for c in mysql_cursor.fetchall()]
    
    # Create Table in SQLite
    sqlite_cursor.execute(f"DROP TABLE IF EXISTS {table}")
    sqlite_cursor.execute(f"CREATE TABLE {table} ({', '.join(cols)})")
    
    # Insert Data
    placeholders = ", ".join(["?"] * len(cols))
    sqlite_cursor.executemany(f"INSERT INTO {table} VALUES ({placeholders})", cleaned_rows)

sqlite_db.commit()
print("✅ SUCCESS! sakila.db created successfully")

# Close connections
mysql_db.close()
sqlite_db.close()