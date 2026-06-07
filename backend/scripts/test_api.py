import os
import requests
import json

def test_api():
    print("Testing /api/search API endpoint directly...")
    file_path = r"d:\PTIT\kì 2 năm 4\Cơ sở dữ liệu đa phương tiện\CSDLDPT\dataset\Viola\viola_ord_A#3_ff_821.wav"
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return

    url = "http://127.0.0.1:8000/api/search"
    with open(file_path, "rb") as f:
        files = {"file": f}
        try:
            response = requests.post(url, files=files)
            if response.status_code != 200:
                print(f"API Error {response.status_code}: {response.text}")
                return
            
            data = response.json()
            print("API Success. Checking response structure...")
            
            # Check Query Data
            q = data.get("query", {})
            print(f"Query pitch_vector length: {len(q.get('pitch_vector', []))}")
            print(f"Query timbre_vector length: {len(q.get('timbre_vector', []))}")
            print(f"Query raw_timbre length: {len(q.get('raw_timbre', []))}")
            
            # Check Results Data
            results = data.get("search_results", [])
            print(f"\nNumber of results: {len(results)}")
            if len(results) > 0:
                first_res = results[0]
                print(f"Result #1 ({first_res['file_name']}):")
                print(f"  - pitch_vector length: {len(first_res.get('pitch_vector', []))}")
                print(f"  - timbre_vector length: {len(first_res.get('timbre_vector', []))}")
                
                if len(first_res.get('pitch_vector', [])) == 0 or len(first_res.get('timbre_vector', [])) == 0:
                    print("\n[CRITICAL ERROR] The backend is returning empty vectors for the database results!")
                    print("This is exactly why the EQ Board is crashing on the frontend.")
                else:
                    print("\n[OK] The backend is returning properly sized vectors.")
                    
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    test_api()
