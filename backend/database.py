"""
Kết nối PostgreSQL + pgvector.
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from backend.config import DATABASE_URL


def get_connection():
    """Tạo kết nối mới tới PostgreSQL."""
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def execute_query(query: str, params=None, fetch=False):
    """Chạy một câu SQL đơn lẻ."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if fetch:
                result = cur.fetchall()
            else:
                result = None
            conn.commit()
        return result
    finally:
        conn.close()


def run_migrations(migrations_dir: str):
    """Chạy toàn bộ file .sql trong thư mục migrations theo thứ tự."""
    import os
    import glob

    sql_files = sorted(glob.glob(os.path.join(migrations_dir, "*.sql")))
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for sql_file in sql_files:
                print(f"  ▶ Running: {os.path.basename(sql_file)}")
                with open(sql_file, "r", encoding="utf-8") as f:
                    cur.execute(f.read())
            conn.commit()
        print(f"  ✅ Đã chạy xong {len(sql_files)} migrations.")
    finally:
        conn.close()
