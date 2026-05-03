"""
Migration script để chuyển đổi pitch_vector từ 3D xuống 1D.
Không cần extract lại toàn bộ dữ liệu.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.database import get_connection

def migrate():
    conn = get_connection()
    cur = conn.cursor()
    
    print("Bắt đầu chuyển đổi Pitch Vector 3D -> 1D...")
    try:
        # 1. Xóa index cũ
        print("1. Xóa index cũ...")
        cur.execute("DROP INDEX IF EXISTS idx_pitch_vector;")
        
        # 2. Cắt vector từ 3D xuống 1D
        print("2. Chuyển đổi dữ liệu trong bảng audio_files (Cắt phần tử đầu tiên)...")
        cur.execute("""
            ALTER TABLE audio_files 
            ALTER COLUMN pitch_vector TYPE vector(1) 
            USING ('[' || pitch_vector[1] || ']')::vector;
        """)
        
        # 3. Cập nhật scaler_params
        print("3. Cập nhật bảng scaler_params...")
        cur.execute("""
            UPDATE scaler_params 
            SET mean_vec = ARRAY[mean_vec[1]], std_vec = ARRAY[std_vec[1]], n_dims = 1 
            WHERE version = 10;
        """)
        
        # 4. Tạo lại index
        print("4. Khôi phục index HNSW...")
        cur.execute("""
            CREATE INDEX ON audio_files USING hnsw (pitch_vector vector_l2_ops);
        """)
        
        conn.commit()
        print("✅ Đã hoàn tất! Dữ liệu đã chuyển sang 1D thành công.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Có lỗi xảy ra: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    migrate()
