import os, requests
from dotenv import load_dotenv
load_dotenv()

r = requests.get("https://generativelanguage.googleapis.com/v1beta/models",
                 headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]}, timeout=30)
print(r.status_code)
if r.ok:
    for m in r.json().get("models", []):
        if "generateContent" in m.get("supportedGenerationMethods", []):
            print(m["name"])
else:
    print(r.text[:300])