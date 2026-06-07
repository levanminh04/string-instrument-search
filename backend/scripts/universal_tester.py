"""
 
Universal Tester: Trích xuất vector từ file bên ngoài và tạo SQL cho DBeaver.
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.features.extractor import extract_feature_vector
from backend.search.normalizer import normalize_pitch, normalize_timbre

def generate_test_sql(file_path):
    if not os.path.exists(file_path):
        print(f"❌ File không tồn tại: {file_path}")
        return

    print(f"--- Đang xử lý file: {file_path} ---")
    
    # 1. Trích xuất và chuẩn hóa
    raw_pitch, raw_timbre, _, _ = extract_feature_vector(file_path)
    q_pitch = normalize_pitch(raw_pitch, version=10)
    q_timbre = normalize_timbre(raw_timbre, version=11)

    p_str = str(q_pitch.tolist())
    t_str = str(q_timbre.tolist())

    # 2. Tạo câu lệnh SQL cho DBeaver (Không dùng LIMIT 50 ở CTE để test toàn bộ)
    sql_dbeaver = f"""
-- COPY CÂU LỆNH NÀY VÀO DBEAVER ĐỂ TEST TOÀN BỘ DATABASE
SELECT 
    file_name, 
    instrument, 
    pitch, 
    technique,
    (pitch_vector <-> '{p_str}'::vector) as p_dist,
    (timbre_vector <=> '{t_str}'::vector) as t_dist,
    ((pitch_vector <-> '{p_str}'::vector) * 5.0) + (timbre_vector <=> '{t_str}'::vector) as total_score
FROM audio_files
WHERE pitch_vector IS NOT NULL AND timbre_vector IS NOT NULL
ORDER BY total_score ASC
LIMIT 20; -- Bạn có thể tăng Limit để xem nhiều hơn
    """

    print("\n" + "="*30 + " SQL FOR DBEAVER " + "="*30)
    print(sql_dbeaver)
    print("="*77)
    
    return sql_dbeaver

if __name__ == "__main__":
    # Tự động xác định thư mục gốc của project
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        # File mặc định để bạn test thử ngay lập tức
        path = os.path.join(BASE_DIR, "uploads", "Gtr-ord-A#3-ff-3c-N.wav")
        
    generate_test_sql(path)
