-- migration: 012_refine_to_27d
-- Refine the vector dimensions for TinySOL optimization (27 dimensions)

-- 1. Cleanup existing data to force re-extraction (Tránh lỗi dimension mismatch)
TRUNCATE TABLE audio_files, scaler_params, search_logs RESTART IDENTITY CASCADE;

-- 2. Drop old V2 column (No longer used)
ALTER TABLE audio_files DROP COLUMN IF EXISTS feature_vector_v2;

-- 3. Modify the main feature_vector column to 27 dimensions
ALTER TABLE audio_files ALTER COLUMN feature_vector TYPE vector(27);

-- 4. Re-create the HNSW index for the new 27D vector size
DROP INDEX IF EXISTS idx_audio_features_v1;
CREATE INDEX idx_audio_features_27d ON audio_files USING hnsw (feature_vector vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
