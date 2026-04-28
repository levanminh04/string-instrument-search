"""
Script chạy 1 lần: Fit scaler (Z-Score) trên toàn bộ raw vectors trong DB.
Lưu kết quả mean/std vào bảng scaler_params.
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import get_connection


def fit_scaler(version: int = 1):
    """
    Đọc tất cả raw feature_vector từ DB (23 chiều),
    tính mean/std, lưu vào scaler_params,
    rồi cập nhật lại tất cả vector = Z-Score + L2.
    """
    col = "feature_vector"

    conn = get_connection()
    cur = conn.cursor()

    # 1. Lấy tất cả raw vectors
    cur.execute(f"SELECT id, {col}::text FROM audio_files WHERE {col} IS NOT NULL")
    rows = cur.fetchall()
    print(f"  📊 Đọc được {len(rows)} vector từ DB")

    if len(rows) == 0:
        print("  ❌ Chưa có vector nào trong DB. Hãy chạy batch_extract.py trước!")
        return

    # Parse vectors
    vectors = []
    ids = []
    for row in rows:
        ids.append(row[0])
        vec_str = row[1].strip("[]")
        vec = np.fromstring(vec_str, sep=",")
        vectors.append(vec)

    matrix = np.array(vectors)  # shape = (N, D)
    n_samples, n_dims = matrix.shape
    print(f"  📐 Ma trận: {n_samples} mẫu × {n_dims} chiều")

    # 2. Tính mean và std
    mean_vec = np.mean(matrix, axis=0)
    std_vec = np.std(matrix, axis=0)

    # 3. Lưu vào scaler_params
    cur.execute(
        """
        INSERT INTO scaler_params (version, mean_vec, std_vec, n_dims, n_samples)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (version) DO UPDATE SET
            mean_vec = EXCLUDED.mean_vec,
            std_vec = EXCLUDED.std_vec,
            n_dims = EXCLUDED.n_dims,
            n_samples = EXCLUDED.n_samples
        """,
        (version, mean_vec.tolist(), std_vec.tolist(), n_dims, n_samples),
    )
    print(f"  💾 Đã lưu scaler v{version} vào DB")

    # 4. Chuẩn hóa lại tất cả vectors (Z-Score + L2)
    std_safe = np.where(std_vec == 0, 1.0, std_vec)
    normalized = (matrix - mean_vec) / std_safe
    norms = np.linalg.norm(normalized, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    normalized = normalized / norms

    # 5. UPDATE lại DB
    for i, row_id in enumerate(ids):
        cur.execute(
            f"UPDATE audio_files SET {col} = %s WHERE id = %s",
            (normalized[i].tolist(), row_id),
        )
        if (i + 1) % 100 == 0:
            print(f"  ✅ Đã chuẩn hóa {i + 1}/{n_samples} vector...")
            conn.commit()

    conn.commit()
    cur.close()
    conn.close()
    print(f"  🎉 HOÀN TẤT: Đã chuẩn hóa {n_samples} vector (version={version})")


if __name__ == "__main__":
    v = 1
    if len(sys.argv) > 1:
        v = int(sys.argv[1])
    fit_scaler(version=v)
