-- ============================================================
-- Migration 004: Bảng search_logs
-- Ghi log kết quả tìm kiếm (phục vụ YC 4b — kết quả trung gian)
-- ============================================================
CREATE TABLE IF NOT EXISTS search_logs (
    id                SERIAL PRIMARY KEY,
    query_file_name   TEXT,
    query_vector      FLOAT[],           -- FLOAT[] thay vì vector() → linh hoạt chiều
    result_ids        INT[],             -- [id1, id2, id3, id4, id5]
    similarity_scores FLOAT[],           -- [0.97, 0.94, 0.91, ...]
    vector_version    INT,               -- version nào đã dùng khi search
    search_time_ms    FLOAT,
    created_at        TIMESTAMP DEFAULT NOW()
);
