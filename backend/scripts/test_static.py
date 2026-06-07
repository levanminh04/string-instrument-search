import urllib.request

try:
    js_content = urllib.request.urlopen('http://127.0.0.1:8000/app_v3.js').read().decode('utf-8')
    if "MFCC Std" in js_content:
        print("[SUCCESS] The server is serving the updated app_v3.js with MFCC Std!")
    else:
        print("[FAIL] The server is NOT serving the updated app_v3.js! It might be serving a cached version.")
        
    if "inVec.length < 19" in js_content:
        print("[SUCCESS] The server is serving the updated app_v3.js with inVec.length < 19!")
    else:
        print("[FAIL] The server is NOT serving the updated app_v3.js with inVec.length < 19!")
        
except Exception as e:
    print(f"Error fetching: {e}")
