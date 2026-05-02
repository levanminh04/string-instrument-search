"""
Diagnostic: Kiểm tra tại sao query A#3 (MIDI 58) lại trả về B3 (MIDI 59).
Không sửa gì, chỉ đọc dữ liệu và in ra.
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.database import get_connection
from backend.search.normalizer import normalize_pitch

conn = get_connection()
cur = conn.cursor()

# === CHECK 1: Có bao nhiêu file A#3 trong DB? ===
print("=" * 60)
print("CHECK 1: Có file A#3 nào trong database không?")
print("=" * 60)
cur.execute("SELECT file_name, pitch, instrument, dynamics FROM audio_files WHERE pitch = 'A#3' OR pitch = 'Bb3'")
rows = cur.fetchall()
print(f"  Tìm thấy {len(rows)} file A#3/Bb3")
for r in rows[:10]:
    print(f"    {r[0]} | {r[1]} | {r[2]} | {r[3]}")

# === CHECK 2: Pitch vector thực tế trong DB cho A#3 vs B3 ===
print("\n" + "=" * 60)
print("CHECK 2: So sánh pitch_vector (Z-Scored) giữa A#3 và B3")
print("=" * 60)

cur.execute("SELECT file_name, pitch, pitch_vector::text FROM audio_files WHERE pitch = 'A#3' LIMIT 3")
a_rows = cur.fetchall()
cur.execute("SELECT file_name, pitch, pitch_vector::text FROM audio_files WHERE pitch = 'B3' LIMIT 3")
b_rows = cur.fetchall()

print("  --- A#3 files ---")
for r in a_rows:
    print(f"    {r[0]} | pitch_vector = {r[2]}")
print("  --- B3 files ---")
for r in b_rows:
    print(f"    {r[0]} | pitch_vector = {r[2]}")

# === CHECK 3: Scaler params cho pitch (v10) ===
print("\n" + "=" * 60)
print("CHECK 3: Scaler params (version=10) cho Pitch")
print("=" * 60)
cur.execute("SELECT mean_vec, std_vec, n_dims, n_samples FROM scaler_params WHERE version = 10")
row = cur.fetchone()
if row:
    mean = np.array(row[0])
    std = np.array(row[1])
    print(f"  mean = {mean}")
    print(f"  std  = {std}")
    print(f"  n_dims = {row[2]}, n_samples = {row[3]}")
    
    # Mô phỏng Z-Score cho MIDI 58 (A#3) và MIDI 59 (B3)
    query_raw = np.array([58.0, 58.0, 58.0])
    query_z = (query_raw - mean) / np.where(std == 0, 1.0, std)
    print(f"\n  Query A#3 (raw=[58,58,58]) → Z-Score = {query_z}")
    
    b3_raw = np.array([59.0, 59.0, 59.0])
    b3_z = (b3_raw - mean) / np.where(std == 0, 1.0, std)
    print(f"  B3     (raw=[59,59,59]) → Z-Score = {b3_z}")
    
    euclidean_dist = np.linalg.norm(query_z - b3_z)
    print(f"  Euclidean distance (A#3 vs B3 after Z-Score) = {euclidean_dist:.4f}")
else:
    print("  ❌ Không tìm thấy scaler v10!")

# === CHECK 4: Thực thi SQL filter-and-rank giống similarity.py ===
print("\n" + "=" * 60)
print("CHECK 4: Chạy Stage 1 (Pitch Filter) trực tiếp")
print("=" * 60)

# Chuẩn hóa query pitch
query_raw = np.array([58.0, 58.0, 58.0], dtype=np.float32)
query_norm = normalize_pitch(query_raw, version=10)
print(f"  Query normalized pitch = {query_norm}")
p_str = str(query_norm.tolist())

cur.execute(f"""
    SELECT file_name, pitch, instrument, dynamics,
           (pitch_vector <-> '{p_str}'::vector) as pitch_dist
    FROM audio_files
    WHERE pitch_vector IS NOT NULL
    ORDER BY pitch_vector <-> '{p_str}'::vector
    LIMIT 15
""")
rows = cur.fetchall()
print(f"\n  Top 15 kết quả Stage 1 (Pitch Filter - Euclidean):")
for i, r in enumerate(rows):
    print(f"    #{i+1:2d} | dist={r[4]:.4f} | {r[2]:15s} | {r[1]:5s} | {r[3]:3s} | {r[0]}")

cur.close()
conn.close()
