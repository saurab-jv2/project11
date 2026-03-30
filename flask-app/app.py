import os
import json
import redis
import psycopg2
from flask import Flask, jsonify

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_NAME = os.getenv("DB_NAME", "appdb")
DB_USER = os.getenv("POSTGRES_USER", "appuser")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "apppass")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )


@app.route("/")
def home():
    return jsonify({"message": "Flask app is running"})


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/redis-test")
def redis_test():
    redis_client.set("test_key", "Redis is working")
    value = redis_client.get("test_key")
    return jsonify({"redis_value": value})


@app.route("/db-test")
def db_test():
    cache_key = "db_test_table_rows"

    cached_data = redis_client.get(cache_key)
    if cached_data:
        return jsonify({
            "source": "redis-cache",
            "data": json.loads(cached_data)
        })

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, created_at FROM test_table ORDER BY id;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "id": row[0],
            "name": row[1],
            "created_at": row[2].isoformat() if row[2] else None
        })

    redis_client.setex(cache_key, 60, json.dumps(result))

    return jsonify({
        "source": "postgres",
        "data": result
    })