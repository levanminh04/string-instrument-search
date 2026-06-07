"""
Test Weighted Scoring: Kiểm chứng nốt A#3 thắng nốt B3 nhờ trọng số.
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import get_connection
from backend.features.extractor import extract_feature_vector
from backend.search.normalizer import normalize_pitch, normalize_timbre

def test():
    # Tự động xác định thư mục gốc của project
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # 1. File test gây lỗi trước đó
    test_file = os.path.join(BASE_DIR, "uploads", "Va-pont-A#3-mf-3c-N.wav")
    if not os.path.exists(test_file): 
        print(f"❌ Không tìm thấy file {test_file}. Hãy đảm bảo bạn đã upload file này.")
        return

    print(f"--- Đang test file: {test_file} ---")
    raw_pitch, raw_timbre, _, _ = extract_feature_vector(test_file)
    q_pitch = normalize_pitch(raw_pitch, version=10)
    q_timbre = normalize_timbre(raw_timbre, version=11)

    p_str = str(q_pitch.tolist())
    t_str = str(q_timbre.tolist())

    # 2. Query trực tiếp để lấy cả các chỉ số trung gian
    conn = get_connection()
    from psycopg2.extras import RealDictCursor
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print(f"\n{'Hạng':<5} | {'Điểm Tổng':<10} | {'P-Dist':<8} | {'T-Dist':<8} | {'Nốt':<5} | {'File'}")
    print("-" * 85)

    query = """
        WITH pitch_filtered AS (
            SELECT
                file_name, pitch, instrument,
                pitch_vector, timbre_vector,
                (pitch_vector <-> %s::vector) as p_dist
            FROM audio_files
            WHERE pitch_vector IS NOT NULL AND timbre_vector IS NOT NULL
            ORDER BY pitch_vector <-> %s::vector
            LIMIT 50
        )
        SELECT
            file_name, pitch, instrument, p_dist,
            (timbre_vector <=> %s::vector) as t_dist,
            ((p_dist * 5.0) + (timbre_vector <=> %s::vector)) as total_score
        FROM pitch_filtered
        ORDER BY total_score ASC
        LIMIT 5;
    """
    
    cur.execute(query, (p_str, p_str, t_str, t_str))
    results = cur.fetchall()

    for i, r in enumerate(results):
        print(f"#{i+1:<4} | {r['total_score']:<10.4f} | {r['p_dist']:<8.4f} | {r['t_dist']:<8.4f} | {r['pitch']:<5} | {r['file_name']}")

    print("\nGiải thích cho báo cáo:")
    print("- total_score = (P-Dist * 5.0) + T-Dist")
    print("- P-Dist (Pitch Distance): Càng thấp nốt càng chuẩn.")
    print("- T-Dist (Timbre Distance): Càng thấp âm sắc càng giống.")
    print("- Kết quả: Các file chuẩn nốt A#3 (P-Dist = 0) sẽ có lợi thế cực lớn.")

    cur.close()
    conn.close()

if __name__ == "__main__":
    test()
