-- migration: 013_refine_to_23d
-- Chuyển từ 27 chiều sang 23 chiều theo feature proposal

-- 1. Cleanup existing data to force re-extraction
TRUNCATE TABLE audio_files, scaler_params, search_logs RESTART IDENTITY CASCADE;

-- 2. Modify the main feature_vector column to 23 dimensions
ALTER TABLE audio_files ALTER COLUMN feature_vector TYPE vector(23);

-- 3. Re-create the HNSW index (CẦN CHẠY SAU KHI ĐÃ CÓ DATA VÀ CHUẨN HÓA)
DROP INDEX IF EXISTS idx_audio_features_23d;
CREATE INDEX idx_audio_features_23d ON audio_files USING hnsw (feature_vector vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

