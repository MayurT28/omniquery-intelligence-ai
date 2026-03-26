import os
import sqlite3
import mysql.connector
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    """Helper to return the correct connection object."""
    if os.path.exists("sakila.db"):
        return sqlite3.connect("sakila.db")
    else:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password=os.getenv("DB_PASSWORD"),
            database="sakila"
        )

def run_query(query):
    conn = get_connection()
    try:
        if os.path.exists("sakila.db"):
            # SQLite Path
            df = pd.read_sql_query(query, conn)
            return df.to_dict(orient="records")
        else:
            # MySQL Path
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            result = cursor.fetchall()
            return result
    finally:
        conn.close()

def get_db_schema(db_name):
    """Fetches schema differently based on DB type."""
    if os.path.exists("sakila.db"):
        # SQLite way to get table and column info
        query = """
        SELECT m.name as table_name, 
        (SELECT GROUP_CONCAT(name, ', ') FROM pragma_table_info(m.name)) as columns
        FROM sqlite_master m WHERE m.type='table' AND m.name NOT LIKE 'sqlite_%';
        """
        return run_query(query)
    else:
        # MySQL way (Your original code)
        clean_name = db_name.lower() 
        query = f"""
        SELECT table_name, GROUP_CONCAT(column_name SEPARATOR ', ') as columns
        FROM information_schema.columns
        WHERE table_schema = '{clean_name}'
        GROUP BY table_name;
        """
        return run_query(query)

def get_db_fingerprint():
    """Generates a unique ID for the DB state."""
    if os.path.exists("sakila.db"):
        # Just use the file modification time as a fingerprint for SQLite
        return f"sqlite-{os.path.getmtime('sakila.db')}"
    else:
        query = """
        SELECT CONCAT(DATABASE(), '-', IFNULL(MAX(UPDATE_TIME), '0'), '-', MAX(CREATE_TIME)) as fp
        FROM information_schema.tables 
        WHERE TABLE_SCHEMA = DATABASE();
        """
        try:
            result = run_query(query)
            return str(result[0]['fp']) if result else "no_fp"
        except:
            return "default_fp"