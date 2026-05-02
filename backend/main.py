import os
import shutil
import time
import urllib.parse
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# Sửa lỗi đường dẫn module khi chạy uvicorn
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import UPLOAD_DIR, BASE_DIR, PITCH_DIM, TIMBRE_DIM
from backend.features.extractor import extract_feature_vector
from backend.search.normalizer import normalize_pitch, normalize_timbre
from backend.search.similarity import search_similar

app = FastAPI(title="Violin & String Instrument Finder")

def parse_filename_metadata(filename: str):
    """Cố gắng phân tích metadata từ tên file TinySOL (ví dụ: viola_ord_A#3_ff_851.wav)"""
    parts = filename.replace(".wav", "").split("_")
    meta = {
        "instrument": "Unknown",
        "technique": "Unknown",
        "pitch": "Unknown",
        "dynamics": "Unknown",
        "string_id": "Unknown"
    }
    # Tinh gọn: TinySOL ord format: {inst}_{ord}_{pitch}_{dyn}_{id}
    if len(parts) >= 4:
        meta["instrument"] = parts[0].capitalize()
        # Mở rộng ord thành ordinario để hiển thị đẹp hơn
        meta["technique"] = "ordinario" if parts[1] == "ord" else parts[1]
        meta["pitch"] = parts[2]
        meta["dynamics"] = parts[3]
        
    # Attempt to fetch exact metadata from DB if it exists
    try:
        from backend.database import get_connection
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT instrument, technique, pitch, dynamics, string_id FROM audio_files WHERE file_name = %s LIMIT 1", (filename,))
            row = cur.fetchone()
            if row:
                meta["instrument"] = row[0] if row[0] else meta["instrument"]
                meta["technique"] = row[1] if row[1] else meta["technique"]
                meta["pitch"] = row[2] if row[2] else meta["pitch"]
                meta["dynamics"] = row[3] if row[3] else meta["dynamics"]
                if row[4] is not None:
                    meta["string_id"] = int(row[4])
        conn.close()
    except Exception as e:
        pass
        
    return meta

@app.post("/api/search")
async def search_audio(file: UploadFile = File(...)):
    """API Nhận file âm thanh, trả về top kết quả (Multi-Vector 3D+18D)."""
    start_api = time.perf_counter()
    
    # 1. Lưu file tạm
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Phân tích metadata từ tên file để hiển thị cho người dùng
    input_meta = parse_filename_metadata(file.filename)
        
    # 2. Extract Vector thô
    try:
        raw_pitch, raw_timbre, rms_mean, actual_sec = extract_feature_vector(file_path)
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Lỗi trích xuất âm thanh: {str(e)}"})
        
    # 3. Chuẩn hóa Pitch và Timbre riêng biệt
    clean_pitch = normalize_pitch(raw_pitch, version=10)
    clean_timbre = normalize_timbre(raw_timbre, version=11)
    
    # 4. Tìm kiếm trong Database bằng Filter-and-Rank
    results = search_similar(clean_pitch, clean_timbre, top_k=6)
    
    # Thêm đường dẫn file cho kết quả
    for res in results["results"]:
        instrument_dir = res["instrument"]
        file_name = res["file_name"]
        encoded_path = urllib.parse.quote(f"{instrument_dir}/{file_name}")
        res["audio_url"] = f"/dataset/{encoded_path}"
    
    total_ms = (time.perf_counter() - start_api) * 1000
    
    encoded_upload = urllib.parse.quote(file.filename)
    return JSONResponse(content={
        "query": {
            "file_name": file.filename,
            "audio_url": f"/uploads/{encoded_upload}",
            "pitch_vector": clean_pitch.tolist(),
            "timbre_vector": clean_timbre.tolist(),
            "raw_pitch": raw_pitch.tolist(),
            "raw_timbre": raw_timbre.tolist(),
            "rms_mean": rms_mean,
            "extract_sec": round(actual_sec, 2),
            "dimensions": f"{PITCH_DIM}D + {TIMBRE_DIM}D",
            "metadata": input_meta
        },
        "search_results": results["results"],
        "timing": {
            "db_search_ms": results["search_time_ms"],
            "total_api_ms": round(total_ms, 2)
        }
    })

# Phục vụ thư mục dataset và uploads để Frontend Play được nhạc
app.mount("/dataset", StaticFiles(directory=os.path.join(BASE_DIR, "dataset")), name="dataset")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Phục vụ thư mục Frontend (HTML, CSS, JS) cho trang chủ
# LƯU Ý: Frontend mount PHẢI nằm dưới cùng để không chèn lên các API khác
app.mount("/", StaticFiles(directory=os.path.join(BASE_DIR, "frontend"), html=True), name="frontend")
