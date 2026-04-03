from fastapi import FastAPI
from brain import get_sql_from_ai
from database import run_query, get_db_fingerprint

app = FastAPI()


@app.get("/")
def root():
    return {"message": "OmniQuery API running successfully"}


@app.get("/query")
def query(question: str):

    fingerprint = get_db_fingerprint()

    sql = get_sql_from_ai(
        question,
        "Tables: film, actor, category, customer, rental, payment, inventory",
        fingerprint
    )

    results = run_query(sql)

    return {
        "question": question,
        "generated_sql": sql,
        "results": results
    }