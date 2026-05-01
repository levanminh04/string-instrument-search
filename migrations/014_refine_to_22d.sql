-- migration: 014_refine_to_22d
-- Chuyển từ 23 chiều sang 22 chiều (Loại bỏ Attack Time)

-- 1. Xóa index cũ
DROP INDEX IF EXISTS idx_audio_features_23d;
DROP INDEX IF EXISTS idx_audio_features_22d; -- Xóa nếu đã lỡ tạo

-- 2. Xóa dữ liệu cũ
TRUNCATE TABLE audio_files, scaler_params, search_logs RESTART IDENTITY CASCADE;

-- 3. Cập nhật lại cột feature_vector thành 22 chiều
ALTER TABLE audio_files ALTER COLUMN feature_vector TYPE vector(22);

-- 4. Tạo index mới cho 22 chiều
CREATE INDEX idx_audio_features_22d ON audio_files USING hnsw (feature_vector vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
