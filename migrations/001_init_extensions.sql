-- ============================================================
-- Migration 001: Khởi tạo Extension pgvector
-- ============================================================
-- pgvector cho phép lưu trữ và tìm kiếm vector trong PostgreSQL
CREATE EXTENSION IF NOT EXISTS vector;
