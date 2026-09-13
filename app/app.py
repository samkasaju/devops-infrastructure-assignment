import os
import socket
import shutil
import time

import psycopg2
from flask import Flask, jsonify

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "traineedb")
DB_USER = os.getenv("POSTGRES_USER", "trainee")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "")


def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        connect_timeout=3,
    )


def init_db():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS visits ("
            "id SERIAL PRIMARY KEY, "
            "visited_at TIMESTAMPTZ NOT NULL DEFAULT NOW())"
        )
        conn.commit()


@app.route("/")
def index():
    return jsonify(
        service="devops-trainee-backend",
        served_by=socket.gethostname(),
        message="Request reached the Flask backend through the Nginx reverse proxy.",
    )


@app.route("/health")
def health():
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return jsonify(status="ok", database="reachable"), 200
    except Exception as exc:
        return jsonify(status="degraded", database=str(exc)), 503



@app.route("/metrics")
def metrics():
    load_1, load_5, load_15 = os.getloadavg()

    memory = {}
    with open("/proc/meminfo") as f:
        for line in f:
            key, value = line.split(":", 1)
            if key in ("MemTotal", "MemAvailable"):
                memory[key] = int(value.strip().split()[0]) * 1024

    mem_total = memory["MemTotal"]
    mem_available = memory["MemAvailable"]
    mem_used = mem_total - mem_available
    mem_percent = (mem_used / mem_total) * 100

    disk = shutil.disk_usage("/")
    disk_percent = (disk.used / disk.total) * 100

    with open("/proc/uptime") as f:
        uptime_seconds = float(f.read().split()[0])

    return jsonify(
        cpu_load_1m=round(load_1, 2),
        cpu_load_5m=round(load_5, 2),
        cpu_load_15m=round(load_15, 2),
        memory_used_percent=round(mem_percent, 2),
        disk_used_percent=round(disk_percent, 2),
        uptime_seconds=round(uptime_seconds, 2),
        timestamp=int(time.time()),
    )


@app.route("/visits")
def visits():
    """Increments a counter in Postgres. Proves the volume survives a restart."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO visits DEFAULT VALUES")
        cur.execute("SELECT COUNT(*) FROM visits")
        total = cur.fetchone()[0]
        conn.commit()
    return jsonify(total_visits=total)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.getenv("APP_PORT", 5000)))
