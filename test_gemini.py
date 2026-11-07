import os, time, requests
from dotenv import load_dotenv
load_dotenv()

headers = {"x-goog-api-key": os.environ["GEMINI_API_KEY"], "Content-Type": "application/json"}
r = requests.get("https://generativelanguage.googleapis.com/v1beta/models", headers=headers, timeout=30)
names = [m["name"].replace("models/", "") for m in r.json().get("models", [])
         if "generateContent" in m.get("supportedGenerationMethods", []) and "flash" in m["name"]]

for name in names[:8]:
    start = time.time()
    try:
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{name}:generateContent",
            headers=headers,
            json={"contents": [{"parts": [{"text": "Say hello in five words."}]}]},
            timeout=20,
        )
        print(f"{name}: {resp.status_code} in {time.time() - start:.1f}s")
    except Exception as e:
        print(f"{name}: failed ({type(e).__name__})")