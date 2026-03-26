import mysql.connector
import os
from dotenv import load_dotenv
import sqlite3
import pandas as pd

load_dotenv()

def run_query(query):
    # PATH CHECK: If sakila.db exists, we are on GitHub/Streamlit
    if os.path.exists("sakila.db"):
        conn = sqlite3.connect("sakila.db")
        # SQLite returns results slightly differently, so we use Pandas for consistency
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.to_dict(orient="records")
    
    # OTHERWISE: We are on Mayur's local computer using MySQL
    else:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=os.getenv("DB_PASSWORD"), # Ensure this is in your local .env
            database="sakila"
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        conn.close()
        return result

def get_db_schema(db_name):
    # Force lowercase to ensure it matches the internal schema
    clean_name = db_name.lower() 
    query = f"""
    SELECT table_name, GROUP_CONCAT(column_name SEPARATOR ', ') as columns
    FROM information_schema.columns
    WHERE table_schema = '{clean_name}'
    GROUP BY table_name;
    """
    return run_query(query)

def get_db_fingerprint():
    """
    Creates a unique string based on the current database name and the 
    last time any table was updated or created.
    """
    # Added an alias 'fp' to the CONCAT so we can easily grab it from the dictionary
    query = """
    SELECT CONCAT(DATABASE(), '-', IFNULL(MAX(UPDATE_TIME), '0'), '-', MAX(CREATE_TIME)) as fp
    FROM information_schema.tables 
    WHERE TABLE_SCHEMA = DATABASE();
    """
    try:
        # Call run_query directly since it's in the same file
        result = run_query(query)
        
        # Since run_query uses dictionary=True, we access by the key 'fp'
        if result and result[0]['fp']:
            return str(result[0]['fp'])
        return "no_data_fingerprint"
    except Exception as e:
        # Fallback if the database is empty or connection fails
        return f"error_fp_{str(e)[:10]}"