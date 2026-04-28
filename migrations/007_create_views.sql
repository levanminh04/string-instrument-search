-- ============================================================
-- Migration 007: Views
-- ============================================================

-- View tách chi tiết từng chiều (phục vụ YC 4b — kết quả trung gian)
CREATE OR REPLACE VIEW v_feature_detail AS
SELECT
    id, file_name, instrument, technique, pitch, dynamics,
    feature_vector[1]  AS attack_time,
    feature_vector[2]  AS mfcc_mean_1,
    feature_vector[15] AS mfcc_std_1,
    feature_vector[28] AS contrast_1,
    feature_vector[35] AS spectral_centroid,
    feature_vector[36] AS zcr,
    feature_vector[37] AS rms_std,
    vector_version
FROM audio_files
WHERE vector_version = 1;

-- View thống kê dataset (phục vụ YC 1 + YC 5)
CREATE OR REPLACE VIEW v_dataset_stats AS
SELECT
    instrument,
    technique,
    dynamics,
    COUNT(*)                                AS n_files,
    ROUND(AVG(duration_sec)::numeric, 2)    AS avg_duration,
    ROUND(MIN(duration_sec)::numeric, 2)    AS min_duration,
    ROUND(MAX(duration_sec)::numeric, 2)    AS max_duration
FROM audio_files
GROUP BY instrument, technique, dynamics
ORDER BY instrument, technique, dynamics;

-- View lịch sử tìm kiếm kèm tên file kết quả (phục vụ YC 4b)
CREATE OR REPLACE VIEW v_search_results AS
SELECT
    sl.id AS search_id,
    sl.query_file_name,
    sl.similarity_scores,
    sl.search_time_ms,
    sl.created_at,
    af.file_name AS result_file,
    af.instrument AS result_instrument
FROM search_logs sl,
     LATERAL unnest(sl.result_ids) WITH ORDINALITY AS r(file_id, rank)
JOIN audio_files af ON af.id = r.file_id
ORDER BY sl.id, r.rank;
