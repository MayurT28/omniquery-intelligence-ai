import os
import logging
import re
import streamlit as st
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Configure logging for the terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the Gemini Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

@st.cache_data(show_spinner=False)
def get_sql_from_ai(user_question, schema_info, db_fingerprint):
    """
    Generates SQL from natural language. 
    Cached by user_question AND db_fingerprint. 
    If either changes, a new API call is made.
    """
    logging.info(f"🧠 AI is generating SQL for: '{user_question}' (FP: {db_fingerprint})")
    
    system_instruction = f"""
    You are a SQL-ONLY generator for MySQL Sakila. 
    Schema: {schema_info}
    
    STRICT RULE: Return ONLY the SQL query. 
    Do NOT include any greetings, markdown (```), or explanations.
    Your response must start with 'SELECT'.
    """
    
    try:
        # Using the lite model for faster response and lower quota impact
        response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=f"{system_instruction}\n\nQuestion: {user_question}"
        )
        
        # --- THE CLEANING LOGIC ---
        text = response.text.strip()
        
        # Use Regex to extract the SQL starting from SELECT
        match = re.search(r"(SELECT.*)", text, re.IGNORECASE | re.DOTALL)
        
        if match:
            sql = match.group(1)
            # Remove markdown formatting and clean up extra characters
            sql = sql.replace("```sql", "").replace("```", "").split(';')[0] + ";"
            return sql.strip()
        else:
            return "ERROR: No SQL generated. Please rephrase your question."
            
    except Exception as e:
        # This will be caught by the 'except' block in app.py
        logging.error(f"❌ Gemini Error: {e}")
        raise e