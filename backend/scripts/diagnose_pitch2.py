"""
Diagnostic 2: Mô phỏng CHÍNH XÁC luồng API similarity.py
để tìm chỗ B3 lẻn vào kết quả.
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.database import get_connection
from backend.search.normalizer import normalize_pitch, normalize_timbre
from backend.features.extractor import extract_feature_vector

# === Bước 1: Extract từ file thực tế ===
test_file = os.path.join("uploads", "Va+S-ord-A#3-ff-3c-N.wav")
if not os.path.exists(test_file):
    print(f"❌ File {test_file} không tồn tại!")
    sys.exit(1)

print(f"File: {test_file}")
raw_pitch, raw_timbre, rms_mean, sec = extract_feature_vector(test_file)
print(f"Raw Pitch: {raw_pitch}")
print(f"Raw Timbre (first 5): {raw_timbre[:5]}")

# === Bước 2: Normalize ===
clean_pitch = normalize_pitch(raw_pitch, version=10)
clean_timbre = normalize_timbre(raw_timbre, version=11)
print(f"\nNormalized Pitch: {clean_pitch}")
print(f"Normalized Timbre (first 5): {clean_timbre[:5]}")

p_vec_str = str(clean_pitch.tolist())
t_vec_str = str(clean_timbre.tolist())

# === Bước 3: Chạy ĐÚNG câu SQL từ similarity.py ===
print("\n" + "=" * 60)
print("CHẠY ĐÚNG SQL CTE TỪ similarity.py")
print("=" * 60)

conn = get_connection()
from psycopg2.extras import RealDictCursor
cur = conn.cursor(cursor_factory=RealDictCursor)
cur.execute("SET hnsw.ef_search = 400;")

# Trước hết: xem CTE trả về gì (chỉ Stage 1)
print("\n--- CTE pitch_filtered (Top 10) ---")
cur.execute(f"""
    SELECT file_name, pitch, instrument, dynamics,
           (pitch_vector <-> %s::vector) as pitch_dist
    FROM audio_files
    WHERE pitch_vector IS NOT NULL AND timbre_vector IS NOT NULL
    ORDER BY pitch_vector <-> %s::vector
    LIMIT 50
""", (p_vec_str, p_vec_str))
cte_rows = cur.fetchall()
for i, r in enumerate(cte_rows[:10]):
    print(f"  #{i+1:2d} | dist={r['pitch_dist']:.6f} | {r['instrument']:15s} | {r['pitch']:5s} | {r['dynamics']:3s} | {r['file_name']}")
print(f"  ... total: {len(cte_rows)} rows in CTE")

# Đếm pitch distribution trong CTE
pitch_counts = {}
for r in cte_rows:
    p = r['pitch']
    pitch_counts[p] = pitch_counts.get(p, 0) + 1
print(f"\n  Pitch distribution trong CTE 50:")
for p, c in sorted(pitch_counts.items()):
    print(f"    {p}: {c} files")

# Bây giờ: chạy full CTE + Stage 2
print("\n--- FULL QUERY (CTE + Timbre Rank) - Top 6 ---")
cur.execute("""
    WITH pitch_filtered AS (
        SELECT
            id, file_name, instrument, technique, pitch, dynamics, string_id,
            pitch_vector, timbre_vector,
            (pitch_vector <-> %s::vector) as pitch_dist
        FROM audio_files
        WHERE pitch_vector IS NOT NULL AND timbre_vector IS NOT NULL
        ORDER BY pitch_vector <-> %s::vector
        LIMIT 50
    )
    SELECT
        id, file_name, instrument, technique, pitch, dynamics, string_id,
        1 - (timbre_vector <=> %s::vector) AS similarity,
        pitch_vector::text AS pitch_vector_text,
        timbre_vector::text AS timbre_vector_text
    FROM pitch_filtered
    ORDER BY timbre_vector <=> %s::vector
    LIMIT %s;
""", (p_vec_str, p_vec_str, t_vec_str, t_vec_str, 6))

results = cur.fetchall()
for i, r in enumerate(results):
    print(f"  #{i+1} | sim={r['similarity']:.4f} | {r['instrument']:15s} | {r['pitch']:5s} | {r['dynamics']:3s} | {r['file_name']}")

cur.close()
conn.close()
