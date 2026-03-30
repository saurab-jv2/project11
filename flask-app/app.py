import os
import time
import redis
import psycopg2
from flask import Flask, jsonify

app = Flask(__name__)

def get_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

DB_HOST = get_env("DB_HOST")
DB_NAME = get_env("DB_NAME")
DB_USER = get_env("DB_USER")
DB_PASS = get_env("DB_PASS")
DB_PORT = int(os.getenv("DB_PORT", "5432"))  # port is fine to default

REDIS_HOST = get_env("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

VISITS_KEY = "visits_count"


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )


def get_redis_client():
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True
    )


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY,
            count BIGINT NOT NULL
        )
    """)

    cur.execute("""
        INSERT INTO visits (id, count)
        VALUES (1, 0)
        ON CONFLICT (id) DO NOTHING
    """)

    conn.commit()
    cur.close()
    conn.close()


def get_db_visits_count():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT count FROM visits WHERE id = 1")
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row is None:
        return 0
    return int(row[0])


def update_db_visits_count(count):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE visits SET count = %s WHERE id = 1", (count,))
    conn.commit()
    cur.close()
    conn.close()


def init_redis_from_db():
    r = get_redis_client()
    current = r.get(VISITS_KEY)

    if current is None:
        db_count = get_db_visits_count()
        r.set(VISITS_KEY, db_count)


@app.route("/")
def home():
    return "<h1>Hello From CI/CD</h1>", 200


@app.route("/live")
def live():
    return jsonify({"status": "live"}), 200


@app.route("/health")
def health():
    status = {
        "app": "ok",
        "postgres": "down",
        "redis": "down"
    }

    http_code = 200

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()
        status["postgres"] = "ok"
    except Exception as e:
        status["postgres"] = f"error: {str(e)}"
        http_code = 500

    try:
        r = get_redis_client()
        r.ping()
        status["redis"] = "ok"
    except Exception as e:
        status["redis"] = f"error: {str(e)}"
        http_code = 500

    return jsonify(status), http_code


@app.route("/visits")
def visits():
    try:
        r = get_redis_client()

        if r.get(VISITS_KEY) is None:
            db_count = get_db_visits_count()
            r.set(VISITS_KEY, db_count)

        count = int(r.incr(VISITS_KEY))
        update_db_visits_count(count)

        return jsonify({
            "visits": count,
            "source": "redis_write_through_cache"
        }), 200

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


init_db()

for _ in range(10):
    try:
        init_redis_from_db()
        break
    except Exception:
        time.sleep(2)
        continue