-- ============================================================
-- Migration 011: Nâng cấp vector (Thêm 1 chiều F0)
-- Giai đoạn 1: 37 -> 38 chiều
-- Giai đoạn 2: 56 -> 57 chiều
-- Xóa toàn bộ dữ liệu hiện tại để bắt đầu extract lại
-- ============================================================

-- Tạm thời drop các bảng để xóa sạch dữ liệu và thay đổi kiểu dữ liệu cột vector
TRUNCATE TABLE audio_files CASCADE;
TRUNCATE TABLE scaler_params CASCADE;
TRUNCATE TABLE search_logs CASCADE;

-- Drop các HNSW index cũ vì dimension đã đổi
DROP INDEX IF EXISTS idx_feature_vector_cosine;
DROP INDEX IF EXISTS idx_feature_vector_v2_cosine;

-- Đổi kiểu cột
ALTER TABLE audio_files 
  ALTER COLUMN feature_vector TYPE vector(38),
  ALTER COLUMN feature_vector_v2 TYPE vector(57);

-- Tạo lại Index
CREATE INDEX idx_feature_vector_cosine ON audio_files
USING ivfflat (feature_vector vector_cosine_ops)
WITH (lists = 10);

CREATE INDEX idx_feature_vector_v2_cosine ON audio_files
USING ivfflat (feature_vector_v2 vector_cosine_ops)
WITH (lists = 10);
