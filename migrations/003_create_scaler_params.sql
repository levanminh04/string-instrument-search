-- ============================================================
-- Migration 003: Bảng scaler_params
-- Lưu mean/std để chuẩn hóa Z-Score cho feature vectors
-- ============================================================
CREATE TABLE IF NOT EXISTS scaler_params (
    id          SERIAL PRIMARY KEY,
    version     INT NOT NULL UNIQUE,     -- khớp với audio_files.vector_version
    mean_vec    FLOAT[] NOT NULL,        -- Vector trung bình
    std_vec     FLOAT[] NOT NULL,        -- Vector độ lệch chuẩn
    n_dims      INT NOT NULL,            -- Số chiều (37 hoặc 56)
    n_samples   INT,                     -- Số file dùng để fit scaler
    created_at  TIMESTAMP DEFAULT NOW()
);
