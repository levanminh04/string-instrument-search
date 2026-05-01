import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import get_connection

def apply_migration():
    sql_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "migrations", "014_refine_to_22d.sql")
    
    if not os.path.exists(sql_path):
        print(f"File not found: {sql_path}")
        return

    print(f"Applying migration: {os.path.basename(sql_path)}...")
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        with open(sql_path, "r", encoding="utf-8") as f:
            sql = f.read()
            cur.execute(sql)
        conn.commit()
        print("Successfully updated Database to 22 dimensions!")
    except Exception as e:
        conn.rollback()
        print(f"Error applying migration: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    apply_migration()
