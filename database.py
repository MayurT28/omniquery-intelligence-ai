def get_db_schema(db_name):
    # Check for SQLite file FIRST
    if os.path.exists("sakila.db"):
        # SQLite doesn't care about 'db_name', it just looks at its own file
        query = """
        SELECT name as table_name, 
        (SELECT GROUP_CONCAT(name, ', ') FROM pragma_table_info(m.name)) as columns
        FROM sqlite_master m WHERE m.type='table' AND m.name NOT LIKE 'sqlite_%';
        """
        # We call the SQLite logic directly to avoid any MySQL interference
        conn = sqlite3.connect("sakila.db")
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.to_dict(orient="records")
    
    else:
        # MySQL Path (Local PC)
        conn = mysql.connector.connect(
            host="localhost", user="root", 
            password=os.getenv("DB_PASSWORD"), database="sakila"
        )
        cursor = conn.cursor(dictionary=True)
        clean_name = db_name.lower() 
        query = f"""
        SELECT table_name, GROUP_CONCAT(column_name SEPARATOR ', ') as columns
        FROM information_schema.columns
        WHERE table_schema = '{clean_name}'
        GROUP BY table_name;
        """
        cursor.execute(query)
        result = cursor.fetchall()
        conn.close()
        return result