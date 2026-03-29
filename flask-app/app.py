from flask import Flask
import psycopg2
import os
import time

app = Flask(__name__)

DB_HOST = os.environ["DB_HOST"]
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASS = os.environ["DB_PASS"]

def get_db_connection():
    for i in range(10):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS
            )
            return conn
        except Exception:
            time.sleep(2)
    raise Exception("Database not reachable")
@app.route("/")
def home():
    return "Hello from Jenkins CI/CD 🚀 \n checking webhook again"

@app.route("/health")
def health():
    return {"status": "ok"}

@app.route("/db-test")
def db_test():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return {"db": result[0]}
    except Exception as e:
        return {"db-error": str(e)}

app.run(host="0.0.0.0", port=5000)