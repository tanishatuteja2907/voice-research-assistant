import os, glob, json, re, time, requests
from dotenv import load_dotenv
load_dotenv()

MODELS = ["gemini-3.1-flash-lite-preview", "gemini-flash-lite-latest", "gemini-3-flash-preview"]
URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
HEADERS = {"x-goog-api-key": os.environ["GEMINI_API_KEY"], "Content-Type": "application/json"}
PROGRESS = "summary_progress.json"

def gemini(prompt, timeout=90):
    for round_ in range(5):
        for model in MODELS:
            try:
                r = requests.post(URL.format(model=model), headers=HEADERS, timeout=timeout,
                                  json={"contents": [{"parts": [{"text": prompt}]}]})
            except requests.RequestException as e:
                print(f"  {model}: {type(e).__name__}")
                continue
            if r.ok:
                parts = r.json()["candidates"][0]["content"]["parts"]
                return "".join(p.get("text", "") for p in parts).strip()
            print(f"  {model}: error {r.status_code}")
        wait = 20 * (round_ + 1)
        print(f"  all models busy, waiting {wait} seconds")
        time.sleep(wait)
    raise RuntimeError("Gemini kept failing, try again later")

def read_text(path):
    if path.endswith(".txt"):
        return open(path, encoding="utf-8", errors="ignore").read()
    from pypdf import PdfReader
    return " ".join((p.extract_text() or "") for p in PdfReader(path).pages)

progress = {}
if os.path.exists(PROGRESS):
    progress = json.load(open(PROGRESS, encoding="utf-8"))

def save_progress():
    json.dump(progress, open(PROGRESS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

summaries = {}
for path in sorted(glob.glob("books/*")):
    name = os.path.basename(path)
    words = re.sub(r"\s+", " ", read_text(path)).split()
    parts = [" ".join(words[i:i + 8000]) for i in range(0, len(words), 8000)]
    print(name, "-", len(parts), "parts")
    minis = []
    for n, part in enumerate(parts, 1):
        key = f"{name}|{n}"
        if key not in progress:
            print(f"  part {n} of {len(parts)}")
            progress[key] = gemini("Summarize this part of a book in 4 sentences. "
                                   "Mention the names of key characters and events.\n\n" + part)
            save_progress()
            time.sleep(4)
        else:
            print(f"  part {n} already done")
        minis.append(progress[key])
    english = gemini("These are summaries of consecutive parts of one book. Write one clear "
                     "summary of the whole book for listening aloud, in at most 8 sentences, "
                     "plain text with no markdown and no bullet points.\n\n" + "\n".join(minis))
    hindi = gemini("Translate into simple spoken Hindi in Devanagari script. "
                   "Output only the translation.\n\n" + english)
    summaries[name] = {"en": english, "hi": hindi}
    json.dump(summaries, open("summaries.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("Saved summaries.json")