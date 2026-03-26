import streamlit as st
import time
import os
import pandas as pd
from brain import get_sql_from_ai
from database import run_query, get_db_schema, get_db_fingerprint
from google import genai
import plotly.express as px
import random

sql = ""
df = pd.DataFrame()

# --- PAGE CONFIG ---
st.set_page_config(page_title="OmniQuery Pro", layout="wide")

# --- 1. INITIALIZE MEMORY ---
if "history" not in st.session_state:
    st.session_state.history = []
# NEW: Store results so they don't disappear when clicking other buttons
if "current_df" not in st.session_state:
    st.session_state.current_df = None
if "current_sql" not in st.session_state:
    st.session_state.current_sql = None

# Initialize Gemini Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# --- 💡 PYTHON MINI-BRAIN ---
def get_python_summary(df):
    """Upgraded Python logic to generate natural-sounding summaries."""
    if df is None or df.empty:
        return "I checked the database, but it looks like there’s no data matching that request right now."
    
    rows, cols = df.shape
    col_names = [c.lower() for c in df.columns]
    
    # 1. Logic for Single Values (e.g., "What is the price of...")
    if rows == 1 and cols == 1:
        val = df.iloc[0, 0]
        return f"I found the specific detail you were looking for: it's **{val}**."

    # 2. Logic for Money/Payments
    if any(word in col_names for word in ['amount', 'payment', 'total', 'sum', 'revenue']):
        total_val = df.iloc[:, -1].sum() # Assumes the last column is the number
        if rows > 1:
            return f"I've analyzed the financial records. The total comes out to **{total_val}** across {rows} different entries."
        return f"The financial record shows a total of **{total_val}**."

    # 3. Logic for People (Customers/Actors)
    if any(word in col_names for word in ['name', 'customer', 'actor', 'first_name']):
        if rows > 5:
            return f"I've pulled up a list of {rows} people for you. The top results include **{df.iloc[0, 0]}** and **{df.iloc[1, 0]}**."
        return f"I found {rows} individuals matching your search. You can see their details in the table below."

    # 4. Logic for Counts (e.g., "How many...")
    if rows > 1:
        # Randomized openings to make it feel less robotic
        openings = [
            f"Alright, I've gathered the data! There are **{rows} items** in total.",
            f"I found **{rows} results** for you. Here is the breakdown:",
            f"The database returned **{rows} records**. I've organized them below."
        ]
        return random.choice(openings)

    return f"I found one matching result with the details you requested."

# --- Sidebar Status ---
with st.sidebar:
    st.title("📊 System Info")
    st.success("🟢 DB: Sakila Connected")
    st.info("📍 Status: Online")
    
    if st.button("♻️ Refresh AI Memory"):
        st.cache_data.clear()
        st.rerun()

    if st.button("🔄 Clear Current Screen"):
        if "query_input" in st.session_state:
            st.session_state["query_input"] = ""
        st.session_state.current_df = None # Clear saved data
        st.rerun()

    st.sidebar.divider()
    with st.sidebar.expander("📂 Live Database Map"):
        try:
            db_name = os.getenv("DB_NAME", "sakila")
            schema_data = get_db_schema(db_name)
            if schema_data:
                for row in schema_data:
                    if isinstance(row, dict):
                        t_name = row.get('table_name') or row.get('TABLE_NAME')
                        cols = row.get('columns') or row.get('COLUMNS')
                    else:
                        t_name = row[0]
                        cols = row[1]
                    st.write(f"**Table:** `{t_name}`")
                    st.caption(f"Columns: {cols}")
                    st.divider()
        except Exception as e:
            st.error(f"Schema Error: {e}")

    st.sidebar.divider()
    st.sidebar.subheader("📜 Query History")
    if not st.session_state.history:
        st.sidebar.info("No queries yet.")
    else:
        for item in reversed(st.session_state.history):
            st.sidebar.write(f"❓ **{item['question']}**")
            st.sidebar.write(f"💡 {item['answer']}")
            st.sidebar.divider()

st.title("🌐 OmniQuery Intelligence")

# --- Main Query Box ---
with st.form("query_box"):
    user_input = st.text_input("Enter your question:", placeholder="e.g. How many movies are there?", key="query_input")
    submitted = st.form_submit_button("Run Query")

if submitted and user_input:
    db_fingerprint = get_db_fingerprint()
    try:
        with st.spinner("AI is analyzing database..."):
            sql = get_sql_from_ai(user_input, "Tables: film, actor, customer, rental, inventory", db_fingerprint)
            data = run_query(sql)

        if data:
            # SAVE TO SESSION STATE (This makes charts/buttons stay visible)
            st.session_state.current_df = pd.DataFrame(data)
            st.session_state.current_sql = sql
            
            direct_answer = get_python_summary(st.session_state.current_df)
            st.session_state.history.append({"question": user_input, "answer": direct_answer})
            st.session_state.history = st.session_state.history[-2:]

        else:
            st.session_state.current_df = None
            st.warning("No data found for that query.")

    except Exception as e:
        if "429" in str(e) or "quota" in str(e).lower():
            st.error("⚠️ Quota Reached!")
            if st.button("🛑 KILL THE PROCESS"):
                st.warning("Process Terminated.")
                st.stop()
            bar = st.progress(0)
            for i in range(20):
                time.sleep(1)
                bar.progress((i + 1) / 20)
            st.rerun()
        else:
            st.error(f"Error: {e}")

# --- DISPLAY SECTION (Outside the 'submitted' block so it stays visible) ---
if st.session_state.current_df is not None:
    df = st.session_state.current_df
    sql = st.session_state.current_sql
    
    # 1. Summary
    st.info(f"💡 **Summary:** {get_python_summary(df)}")

    # 2. ✨ Hybrid AI Insight Button
    if st.button("✨ Get Deep AI Insight"):
        with st.spinner("Gemini is thinking..."):
            # Use the 2026-stable model ID we discussed
            response = client.models.generate_content(
                model="gemini-3-flash-preview", 
                contents=f"Data: {df.to_dict()}. Explain this result in 1 professional sentence."
            )
            st.success(f"🤖 **AI Insight:** {response.text.strip()}")

    import plotly.express as px # Add this to your imports!

# --- 📊 2026 SMART VISUALIZATION ENGINE ---
if st.session_state.current_df is not None:
    df = st.session_state.current_df
    sql = st.session_state.current_sql
    if len(df) > 1 and len(df.columns) >= 2:
        st.write("### 🚀 AI-Driven Insights & Visuals")
        
        # Clean data types (Ensure numbers are numbers)
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='ignore')
        
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'datetime']).columns.tolist()

        if num_cols and cat_cols:
            label, value = cat_cols[0], num_cols[0]
            
            # 1. PIE CHART (Trending for "Market Share" or "Distribution")
            if "category" in label.lower() or "rating" in label.lower() or len(df) < 7:
                fig = px.pie(df, names=label, values=value, hole=0.4, 
                            title=f"Distribution of {value} by {label}",
                            color_discrete_sequence=px.colors.sequential.RdBu)
                st.plotly_chart(fig, use_container_width=True)
                st.caption("🎯 *Pie/Donut Chart: Optimized for proportional distribution.*")

            # 2. AREA CHART (Trending for "Cumulative Trends")
            elif "date" in label.lower() or len(df) > 20:
                fig = px.area(df, x=label, y=value, markers=True,
                            title=f"Growth Trend: {value} over {label}",
                            line_shape="spline") # 2026 "Smooth" UI trend
                st.plotly_chart(fig, use_container_width=True)
                st.caption("🌊 *Area Chart: Optimized for volume and time-series flow.*")

            # 3. INTERACTIVE BAR CHART (Standard Comparison)
            else:
                fig = px.bar(df, x=label, y=value, color=value,
                            title=f"Comparative Analysis: {label}",
                            text_auto='.2s')
                st.plotly_chart(fig, use_container_width=True)
                st.caption("📊 *Interactive Bar Chart: Optimized for direct comparison.*")

# 4. Technical Details
if st.session_state.current_df is not None and not st.session_state.current_df.empty:
    with st.expander("Show Technical Details (SQL & Table)"):
        st.code(sql, language="sql")
        st.dataframe(df)

st.markdown("---")
st.caption("🚀 **OmniQuery Intelligence v1.0** | Designed & Developed by **MayurT28**")