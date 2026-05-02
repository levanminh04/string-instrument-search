"""
Chuẩn hóa vector: Z-Score + L2 Normalize.
"""
import numpy as np
from backend.database import execute_query


def load_scaler(version: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """Load mean/std từ bảng scaler_params."""
    rows = execute_query(
        "SELECT mean_vec, std_vec FROM scaler_params WHERE version = %s",
        (version,),
        fetch=True,
    )
    if not rows:
        raise ValueError(f"Chưa có scaler cho version={version}. Hãy chạy fit_scaler.py trước.")
    row = rows[0]
    return np.array(row["mean_vec"]), np.array(row["std_vec"])


def z_score_normalize(vector: np.ndarray, mean_vec: np.ndarray, std_vec: np.ndarray) -> np.ndarray:
    """Chuẩn hóa Z-Score: (x - mean) / std."""
    std_safe = np.where(std_vec == 0, 1.0, std_vec)  # Tránh chia cho 0
    return (vector - mean_vec) / std_safe


def l2_normalize(vector: np.ndarray) -> np.ndarray:
    """Chuẩn hóa L2: vector / ||vector||."""
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm


def normalize_pitch(raw_pitch: np.ndarray, version: int = 10) -> np.ndarray:
    """Chuẩn hóa Pitch: CHỈ DÙNG Z-Score (Không dùng L2)."""
    mean_vec, std_vec = load_scaler(version)
    return z_score_normalize(raw_pitch, mean_vec, std_vec)


def normalize_timbre(raw_timbre: np.ndarray, version: int = 11) -> np.ndarray:
    """Chuẩn hóa Timbre: Z-Score → L2."""
    mean_vec, std_vec = load_scaler(version)
    z_scored = z_score_normalize(raw_timbre, mean_vec, std_vec)
    return l2_normalize(z_scored)
