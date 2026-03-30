from flask import Flask, jsonify
import os
import json
import redis
import psycopg2

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

REDIS_HOST = get_env("REDIS_HOST")
REDIS_PORT = int(get_env("REDIS_PORT"))

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
    return jsonify({
        "message": "Flask app is running",
        "service": "project1"
    })


@app.route("/health")
def health():
    status = {
        "app": "ok",
        "db": "down",
        "redis": "down"
    }

    http_code = 200

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()
        status["db"] = "ok"
    except Exception as e:
        status["db_error"] = str(e)
        http_code = 500

    try:
        redis_client.ping()
        status["redis"] = "ok"
    except Exception as e:
        status["redis_error"] = str(e)
        http_code = 500

    return jsonify(status), http_code


@app.route("/visits")
def visits():
    try:
        count = redis_client.incr("visits")
        return jsonify({
            "message": "Visit counter working",
            "visits": count
        })
    except Exception as e:
        return jsonify({
            "error": "Redis connection failed",
            "details": str(e)
        }), 500