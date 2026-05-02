import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import get_connection

def apply_migration():
    sql_path = os.path.join("migrations", "015_add_multi_vector.sql")
    print(f"Đang chạy migration: {sql_path}")
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        with open(sql_path, "r", encoding="utf-8") as f:
            sql_content = f.read()
            
        cur.execute(sql_content)
        conn.commit()
        print("✅ Chạy migration 015 thành công! Đã thêm cột pitch_vector và timbre_vector.")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    apply_migration()
