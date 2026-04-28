"""
Tìm kiếm Cosine Similarity qua pgvector.
"""
import time
import numpy as np
from backend.database import get_connection
from backend.config import TOP_K


def search_similar(query_vector: np.ndarray, top_k: int = TOP_K) -> dict:
    """
    Tìm top-K file âm thanh giống nhất bằng Cosine Similarity (23 chiều).
    """
    col = "feature_vector"

    query_str = f"""
        SELECT
            id, file_name, instrument, technique, pitch, dynamics, string_id,
            1 - ({col} <=> %s::vector) AS similarity,
            {col}::text AS feature_vector_text
        FROM audio_files
        WHERE {col} IS NOT NULL
        ORDER BY {col} <=> %s::vector
        LIMIT %s;
    """

    vec_list = query_vector.tolist()
    vec_str = str(vec_list)

    start = time.perf_counter()
    conn = get_connection()
    try:
        from psycopg2.extras import RealDictCursor
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SET hnsw.ef_search = 400;")
            cur.execute(query_str, (vec_str, vec_str, top_k))
            results = cur.fetchall()
            
            # Chạy vòng lặp để chuyển string '[0.1, 0.2, ...]' thành list(float) cho JSON
            for row in results:
                vec_str = row['feature_vector_text'].strip('[]')
                row['feature_vector'] = [float(x) for x in vec_str.split(',')]
                del row['feature_vector_text']  # Xóa cột text dư thừa
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
