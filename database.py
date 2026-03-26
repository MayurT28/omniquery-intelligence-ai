import os
import sqlite3
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def run_query(query):
    # Check if we are on the Cloud (SQLite) or Local (MySQL)
    if os.path.exists("sakila.db"):
        conn = sqlite3.connect("sakila.db")
        # Standard SQLite return (list of tuples)
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        # Convert tuples to dictionaries so app.py doesn't break
        columns = [column[0] for column in cursor.description]
        data = [dict(zip(columns, row)) for row in result]
        conn.close()
        return data
    else:
        # Local MySQL Logic
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=os.getenv("DB_PASSWORD"),
            database="sakila"
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        conn.close()
        return result

def get_db_schema(db_name):
    if os.path.exists("sakila.db"):
        # SQLite Schema Query
        query = "SELECT name as table_name, 'Click to see columns' as columns FROM sqlite_master WHERE type='table';"
        return run_query(query)
    else:
        # MySQL Schema Query
        query = f"SELECT table_name, 'Check MySQL' as columns FROM information_schema.tables WHERE table_schema = '{db_name}';"
        return run_query(query)

def get_db_fingerprint():
    if os.path.exists("sakila.db"):
        return str(os.path.getmtime("sakila.db"))
    return "local-mysql-fp"