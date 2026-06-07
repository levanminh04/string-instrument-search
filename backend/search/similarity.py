"""
Tìm kiếm Cosine Similarity qua pgvector.
"""
import time
import numpy as np
from backend.database import get_connection
from backend.config import TOP_K


def search_similar(pitch_vector: np.ndarray, timbre_vector: np.ndarray, top_k: int = TOP_K) -> dict:
    """
    Tìm top-K file bằng Filter-and-Rank:
    1. Lọc top 50 nốt nhạc gần nhất (Euclidean trên pitch_vector)
    2. Xếp hạng top K âm sắc giống nhất (Cosine trên timbre_vector)
    """
    query_str = f"""
        SELECT
            id, file_name, instrument, technique, pitch, dynamics, string_id,
            pitch_vector::text AS pitch_vector_text,
            timbre_vector::text AS timbre_vector_text,
            (pitch_vector <-> %s::vector) as p_dist,
            (timbre_vector <=> %s::vector) as t_dist,
            ((pitch_vector <-> %s::vector) * 5.0) + (timbre_vector <=> %s::vector) AS total_score
        FROM audio_files
        WHERE pitch_vector IS NOT NULL AND timbre_vector IS NOT NULL
        ORDER BY total_score ASC
        LIMIT %s;
    """

    p_vec_str = str(pitch_vector.tolist())
    t_vec_str = str(timbre_vector.tolist())

    start = time.perf_counter()
    conn = get_connection()
    try:
        from psycopg2.extras import RealDictCursor
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SET hnsw.ef_search = 400;")
            cur.execute(query_str, (p_vec_str, t_vec_str, p_vec_str, t_vec_str, top_k))
            results = cur.fetchall()
            
            for row in results:
                # Trả về giá trị thập phân (0.0 - 1.0), Frontend sẽ tự nhân 100 để hiển thị %
                row['similarity'] = max(0, 1 - row['total_score'])
                
                p_text = row.pop('pitch_vector_text', '[]')
                t_text = row.pop('timbre_vector_text', '[]')
                row['pitch_vector'] = [float(x) for x in p_text.strip('[]').split(',')] if p_text != '[]' else []
                row['timbre_vector'] = [float(x) for x in t_text.strip('[]').split(',')] if t_text != '[]' else []
    finally:
        conn.close()
    elapsed_ms = (time.perf_counter() - start) * 1000

    return {
        "results": results,
        "search_time_ms": round(elapsed_ms, 2),
    }


def log_search(query_file_name: str, query_vector: np.ndarray,
               result_ids: list, similarity_scores: list,
               version: int, search_time_ms: float):
    """Ghi log kết quả tìm kiếm vào bảng search_logs."""
    from backend.database import execute_query
    execute_query(
        """
        INSERT INTO search_logs
            (query_file_name, query_vector, result_ids, similarity_scores, vector_version, search_time_ms)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            query_file_name,
            query_vector.tolist(),
            result_ids,
            similarity_scores,
            version,
            search_time_ms,
        ),
    )
