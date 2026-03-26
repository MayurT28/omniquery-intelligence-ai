import os
from dotenv import load_dotenv
from brain import get_sql_from_ai
from database import run_query
import mysql.connector

load_dotenv()

def get_readonly_schema():
    # This function automatically pulls your table structure
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    cursor = conn.cursor()
    # Query to get all table names in Sakila
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]
    conn.close()
    return ", ".join(tables)

def main():
    print("--- 🌐 OmniQuery AI Agent: Sakila Edition ---")
    
    # 1. Get the list of tables automatically
    schema = get_readonly_schema()
    
    # 2. Get user input
    user_question = input("\nWhat would you like to know from the database? ")
    
    try:
        # 3. Ask AI to generate the SQL
        sql = get_sql_from_ai(user_question, schema)
        print(f"\n[AI Generated SQL]: {sql}")
        
        # 4. Run the SQL on our real Sakila data
        results = run_query(sql)
        
        # 5. Show the results
        print("\n[Database Results]:")
        if results:
            for row in results:
                print(row)
        else:
            print("No data found for this query.")
            
    except Exception as e:
        print(f"\n❌ Something went wrong: {e}")

if __name__ == "__main__":
    main()