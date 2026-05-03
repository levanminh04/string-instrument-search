"""
Script chạy 1 lần: Fit scaler (Z-Score) trên toàn bộ raw vectors trong DB.
Lưu kết quả mean/std vào bảng scaler_params.
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import get_connection
from backend.config import PITCH_DIM


def fit_scaler():
    """
    Đọc tất cả raw pitch_vector và timbre_vector từ DB,
    tính mean/std, lưu vào scaler_params.
    Cập nhật lại DB:
    - pitch_vector = Z-Score
    - timbre_vector = Z-Score + L2
    """
    conn = get_connection()
    cur = conn.cursor()

    # 1. Lấy tất cả vectors
    cur.execute("SELECT id, pitch_vector::text, timbre_vector::text FROM audio_files WHERE pitch_vector IS NOT NULL AND timbre_vector IS NOT NULL")
    rows = cur.fetchall()
    print(f"  📊 Đọc được {len(rows)} vector từ DB")

    if len(rows) == 0:
        print("  ❌ Chưa có vector nào trong DB. Hãy chạy batch_extract.py trước!")
        return

    # Parse vectors
    ids = []
    pitch_vectors = []
    timbre_vectors = []
    for row in rows:
        ids.append(row[0])
        p_str = row[1].strip("[]")
        t_str = row[2].strip("[]")
        pitch_vectors.append(np.fromstring(p_str, sep=","))
        timbre_vectors.append(np.fromstring(t_str, sep=","))

    pitch_matrix = np.array(pitch_vectors)
    timbre_matrix = np.array(timbre_vectors)
    
    n_samples = len(ids)

    # 2. Tính mean và std cho Pitch (v10)
    p_mean = np.mean(pitch_matrix, axis=0)
    p_std = np.std(pitch_matrix, axis=0)
    cur.execute(
        """
        INSERT INTO scaler_params (version, mean_vec, std_vec, n_dims, n_samples)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (version) DO UPDATE SET
            mean_vec = EXCLUDED.mean_vec, std_vec = EXCLUDED.std_vec, n_dims = EXCLUDED.n_dims, n_samples = EXCLUDED.n_samples
        """,
        (10, p_mean.tolist(), p_std.tolist(), PITCH_DIM, n_samples),
    )
    print("  💾 Đã lưu scaler Pitch (v10)")

    # 3. Tính mean và std cho Timbre (v11)
    t_mean = np.mean(timbre_matrix, axis=0)
    t_std = np.std(timbre_matrix, axis=0)
    cur.execute(
        """
        INSERT INTO scaler_params (version, mean_vec, std_vec, n_dims, n_samples)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (version) DO UPDATE SET
            mean_vec = EXCLUDED.mean_vec, std_vec = EXCLUDED.std_vec, n_dims = EXCLUDED.n_dims, n_samples = EXCLUDED.n_samples
        """,
        (11, t_mean.tolist(), t_std.tolist(), 18, n_samples),
    )
    print("  💾 Đã lưu scaler Timbre (v11)")

    # 4. Chuẩn hóa Pitch (Chỉ Z-Score)
    p_std_safe = np.where(p_std == 0, 1.0, p_std)
    norm_pitch = (pitch_matrix - p_mean) / p_std_safe

    # 5. Chuẩn hóa Timbre (Z-Score + L2)
    t_std_safe = np.where(t_std == 0, 1.0, t_std)
    z_timbre = (timbre_matrix - t_mean) / t_std_safe
    t_norms = np.linalg.norm(z_timbre, axis=1, keepdims=True)
    t_norms = np.where(t_norms == 0, 1.0, t_norms)
    norm_timbre = z_timbre / t_norms

    # 6. UPDATE lại DB
    print("  🔄 Bắt đầu cập nhật lại DB...")
    for i, row_id in enumerate(ids):
        cur.execute(
            "UPDATE audio_files SET pitch_vector = %s, timbre_vector = %s WHERE id = %s",
            (norm_pitch[i].tolist(), norm_timbre[i].tolist(), row_id),
        )
        if (i + 1) % 100 == 0:
            print(f"  ✅ Đã chuẩn hóa {i + 1}/{n_samples} vector...")
            conn.commit()

    conn.commit()
    cur.close()
    conn.close()
    print(f"  🎉 HOÀN TẤT: Đã chuẩn hóa Multi-Vector cho {n_samples} bản ghi.")


if __name__ == "__main__":
    fit_scaler()
