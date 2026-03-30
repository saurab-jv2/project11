import logging
import os
import time

import psycopg2
import redis
from flask import Flask, jsonify, g, request

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

VISITS_KEY = "visits"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)


def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        logger.info("DB connection established")
        return conn
    except Exception:
        logger.exception("DB connection failed")
        raise


def get_redis_client():
    try:
        client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )
        client.ping()
        logger.info("Redis connection established")
        return client
    except Exception:
        logger.exception("Redis connection failed")
        raise


def get_db_visits_count():
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT count FROM visits LIMIT 1")
        row = cur.fetchone()
        count = row[0] if row else 0
        logger.info("DB read visits count=%s", count)
        return count
    except Exception:
        logger.exception("DB read for visits failed")
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def increment_db_visits():
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE visits SET count = count + 1 RETURNING count")
        row = cur.fetchone()
        conn.commit()
        count = row[0] if row else 0
        logger.info("DB increment visits count=%s", count)
        return count
    except Exception:
        if conn:
            conn.rollback()
        logger.exception("DB increment for visits failed")
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def init_redis_from_db():
    try:
        r = get_redis_client()
        current = r.get(VISITS_KEY)

        if current is None:
            db_count = get_db_visits_count()
            r.set(VISITS_KEY, db_count)
            logger.info("Redis cache initialized from DB count=%s", db_count)
        else:
            logger.info("Redis cache already initialized count=%s", current)
    except Exception:
        logger.warning("Redis init skipped; app will continue", exc_info=True)


@app.before_request
def before_request_logging():
    g.start_time = time.time()


@app.after_request
def after_request_logging(response):
    duration_ms = round((time.time() - g.start_time) * 1000, 2)
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    logger.info(
        'Request method=%s path=%s status=%s duration_ms=%s ip=%s',
        request.method,
        request.path,
        response.status_code,
        duration_ms,
        client_ip
    )
    return response


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    logger.exception("Unhandled exception on path=%s", request.path)
    return jsonify({"error": "internal server error"}), 500


@app.route("/")
def home():
    logger.info("Home endpoint hit")
    return "<h1>Hello From CI/CD</h1>", 200


@app.route("/live")
def live():
    logger.info("Live endpoint hit")
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
    except Exception:
        logger.exception("Health check failed for Postgres")
        http_code = 503

    try:
        r = get_redis_client()
        r.ping()
        status["redis"] = "ok"
    except Exception:
        logger.exception("Health check failed for Redis")
        http_code = 503

    logger.info("Health status=%s http_code=%s", status, http_code)
    return jsonify(status), http_code


@app.route("/visits")
def visits():
    try:
        r = get_redis_client()

        current = r.get(VISITS_KEY)
        if current is None:
            logger.info("Redis cache miss for visits")
            current_count = increment_db_visits()
            r.set(VISITS_KEY, current_count)
            logger.info("Visits served via DB update and Redis set count=%s", current_count)
            return jsonify({"visits": current_count}), 200

        new_count = r.incr(VISITS_KEY)
        logger.info("Redis increment success visits=%s", new_count)

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("UPDATE visits SET count = %s", (new_count,))
            conn.commit()
            cur.close()
            conn.close()
            logger.info("DB synced with Redis visits=%s", new_count)
        except Exception:
            logger.warning("DB sync failed after Redis increment", exc_info=True)

        return jsonify({"visits": new_count}), 200

    except Exception:
        logger.warning("Redis path failed for /visits, falling back to DB", exc_info=True)
        try:
            db_count = increment_db_visits()
            logger.info("Visits served via DB fallback count=%s", db_count)
            return jsonify({"visits": db_count}), 200
        except Exception:
            logger.exception("Visits endpoint failed completely")
            return jsonify({"error": "unable to update visits"}), 500


logger.info("Flask app starting")
init_redis_from_db()