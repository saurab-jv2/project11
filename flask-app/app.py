import os
import json
import redis
import psycopg2
from flask import Flask, jsonify

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)
import os
import json
import redis
import psycopg2
from flask import Flask, jsonify

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

REDIS_HOST = os.getenv("REDIS_HOST")
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
    return jsonify({"redis_value": redis_client.get("test_key")})


@app.route("/db-test")
def db_test():
    cache_key = "db_test_table_rows"

    cached = redis_client.get(cache_key)
    if cached:
        return jsonify({
            "source": "redis-cache",
            "data": json.loads(cached)
        })

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, created_at FROM test_table ORDER BY id;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    result = [
        {
            "id": r[0],
            "name": r[1],
            "created_at": r[2].isoformat() if r[2] else None
        }
        for r in rows
    ]

    redis_client.setex(cache_key, 60, json.dumps(result))

    return jsonify({
        "source": "postgres",
        "data": result
    })


app.run(host="0.0.0.0", port=5000)

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
    return jsonify({"redis_value": redis_client.get("test_key")})


@app.route("/db-test")
def db_test():
    cache_key = "db_test_table_rows"

    cached = redis_client.get(cache_key)
    if cached:
        return jsonify({
            "source": "redis-cache",
            "data": json.loads(cached)
        })

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, created_at FROM test_table ORDER BY id;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    result = [
        {
            "id": row[0],
            "name": row[1],
            "created_at": row[2].isoformat() if row[2] else None
        }
        for row in rows
    ]

    redis_client.setex(cache_key, 60, json.dumps(result))

    return jsonify({
        "source": "postgres",
        "data": result
    })


app.run(host="0.0.0.0", port=5000)