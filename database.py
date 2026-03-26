import os
import sqlite3
import mysql.connector
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def run_query(query):
    if os.path.exists("sakila.db"):
        conn = sqlite3.connect("sakila.db")
        # Use pandas for consistent dictionary output
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.to_dict(orient="records")
    else:
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
    # 1. SQLITE SCHEMA LOGIC
    if os.path.exists("sakila.db"):
        query = "SELECT name as table_name, sql as columns FROM sqlite_master WHERE type='table';"
        return run_query(query)
    
    # 2. MYSQL SCHEMA LOGIC
    else:
        clean_name = db_name.lower() 
        query = f"""
        SELECT table_name, GROUP_CONCAT(column_name SEPARATOR ', ') as columns
        FROM information_schema.columns
        WHERE table_schema = '{clean_name}'
        GROUP BY table_name;
        """
        return run_query(query)

def get_db_fingerprint():
    # 1. SQLITE FINGERPRINT (Simple version for Cloud)
    if os.path.exists("sakila.db"):
        return f"sqlite-sakila-{os.path.getmtime('sakila.db')}"

    # 2. MYSQL FINGERPRINT (For Mayur's PC)
    else:
        query = """
        SELECT CONCAT(DATABASE(), '-', IFNULL(MAX(UPDATE_TIME), '0'), '-', MAX(CREATE_TIME)) as fp
        FROM information_schema.tables 
        WHERE TABLE_SCHEMA = DATABASE();
        """
        try:
            result = run_query(query)
            if result and 'fp' in result[0]:
                return str(result[0]['fp'])
            return "no_data_fingerprint"
        except Exception:
            return "error_fp_fallback"