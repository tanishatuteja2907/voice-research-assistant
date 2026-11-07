import warnings
warnings.filterwarnings("ignore", message="Reached EOF prematurely")
import os, glob, re, math, collections, msvcrt, logging, time
import numpy as np
import requests
import sounddevice as sd
from scipy.io.wavfile import write, read as wav_read
from dotenv import load_dotenv
load_dotenv()

from gnani.stt import GnaniSTTClient
from gnani.tts import GnaniTTSClient

logging.getLogger("pypdf").setLevel(logging.ERROR)

# ---------- settings ----------
LLM_MODEL = "gemini-3-flash-preview"
FALLBACK_MODELS = ["gemini-flash-lite-latest"]
SILENCE_THRESHOLD = 150
VOICES = {"en": ("Pranav", "en-IN"), "hi": ("Nalini", "hi-IN")}
CORRECTIONS = {"sonali": "Tenali", "core": "court", "queens": "queen"}

MSG = {
    "en": {"nothing_heard": "Sorry, I did not hear anything. Please try again.",
           "not_found": "I could not find that in your books.",
           "error": "Something went wrong. Please try again.",
           "no_repeat": "There is nothing to repeat yet."},
    "hi": {"nothing_heard": "माफ़ कीजिए, मुझे कुछ सुनाई नहीं दिया। कृपया दोबारा कोशिश करें।",
           "not_found": "मुझे यह आपकी किताबों में नहीं मिला।",
           "error": "कुछ गड़बड़ हो गई। कृपया दोबारा कोशिश करें।",
           "no_repeat": "अभी दोहराने के लिए कुछ नहीं है।"},
}

# last answer, stored in both languages (filled in when needed)
LAST = {"en": "", "hi": "", "lang": "en"}

stt = GnaniSTTClient()
tts = GnaniTTSClient()

# ---------- books and search ----------
STOP = set("the a an of to in and is are was were for on with as by at from that "
           "this it be or which what who how why when do does did tell me about".split())
STOP |= set("का की के है हैं में से को और पर यह वह था थी थे क्या कौन कैसे क्यों कब ने भी तो एक कर लिए बारे".split())

def words(text):
    return [w for w in re.findall(r"[\w\u0900-\u0963\u0966-\u097F]+", text.lower())
            if w not in STOP]

def load_chunks(folder="books", size=100, step=70):
    chunks = []
    for path in glob.glob(f"{folder}/*"):
        text = ""
        if path.endswith(".txt"):
            text = open(path, encoding="utf-8", errors="ignore").read()
        elif path.endswith(".pdf"):
            from pypdf import PdfReader
            text = " ".join((p.extract_text() or "") for p in PdfReader(path).pages)
        text = re.sub(r"Reprint 2026-27|Unit \d+\.indd \d+|\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}", " ", text)
        w = text.split()
        for i in range(0, len(w), step):
            chunks.append((os.path.basename(path), " ".join(w[i:i + size])))
    return chunks

def build_index(chunks):
    toks = [words(c[1]) for c in chunks]
    df = collections.Counter()
    for t in toks:
        df.update(set(t))
    n = len(chunks)
    idf = {w: math.log((n + 1) / (c + 0.5)) for w, c in df.items()}
    return toks, idf

def search(question, chunks, toks, idf, k=3):
    q = set(words(question))
    scored = []
    for i, t in enumerate(toks):
        counts = collections.Counter(t)
        s = sum(idf.get(w, 0) * counts[w] / (counts[w] + 1) for w in q if w in counts)
        if s > 0:
            scored.append((s, i))
    scored.sort(reverse=True)
    return [chunks[i] for _, i in scored[:k]]

# ---------- LLM ----------
def call_gemini(prompt):
    for model in [LLM_MODEL] + FALLBACK_MODELS:
        for attempt in range(2):
            try:
                r = requests.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                    headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"],
                             "Content-Type": "application/json"},
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                    timeout=25,
                )
            except requests.RequestException as e:
                print(f"GEMINI {model} failed: {type(e).__name__}")
                break
            if r.ok:
                parts = r.json()["candidates"][0]["content"]["parts"]
                return "".join(p.get("text", "") for p in parts).strip()
            print(f"GEMINI {model} error {r.status_code}: {r.text[:200]}")
            if r.status_code in (429, 500, 503):
                time.sleep(2)
            else:
                break
    raise RuntimeError("All Gemini models failed")

def ask_llm(question, passages, lang):
    context = "\n\n".join(f"[{src}] {txt}" for src, txt in passages)
    if lang == "hi":
        language_rule = ("Reply in Hindi, written in Devanagari script. The passages may be in "
                         "English: use their facts and write the answer in Hindi.")
    else:
        language_rule = "Reply in English."
    prompt = (
        "You are a voice assistant for a visually impaired student. "
        "Answer the question using ONLY the passages below. "
        f"{language_rule} Use at most 4 short sentences, in a plain spoken style, "
        "with no markdown, no bullet points and no symbols. "
        "Answer only what was asked and add no extra details. "
        "If the passages describe different events, use only the passage "
        "that directly answers the question. "
        "If the answer is not in the passages, say you could not find it in the books.\n\n"
        f"Passages:\n{context}\n\nQuestion: {question}"
    )
    return call_gemini(prompt)

def translate_query(question):
    return call_gemini("Translate this Hindi question into simple English. "
                       "Output only the translation.\n\n" + question)

def translate(text, target):
    name = ("simple spoken Hindi written in Devanagari script" if target == "hi"
            else "simple English")
    return call_gemini(f"Translate the following text into {name}. "
                       f"Output only the translation, nothing else.\n\n{text}")

def detect_lang(en, hi):
    try:
        out = call_gemini(
            "The same audio was transcribed by an English speech recognizer and by a Hindi "
            "speech recognizer.\n"
            f"English recognizer: {en}\nHindi recognizer: {hi}\n"
            "Which language did the speaker actually speak? "
            "Answer with exactly one word: english or hindi.")
        return "hi" if "hindi" in out.lower() else "en"
    except Exception as e:
        print("Language detection failed, assuming English:", e)
        return "en"

def detect_command(en, hi):
    if max(len(en.split()), len(hi.split())) > 6:
        return None
    t = f"{en} {hi}".lower()
    if any(w in t for w in ["hindi", "हिंदी", "हिन्दी"]):
        return "hi"
    if any(w in t for w in ["english", "अंग्रेज", "इंग्लिश"]):
        return "en"
    if any(w in t for w in ["repeat", "again", "दोहरा", "दोबारा", "फिर से"]):
        return "same"
    return None

# ---------- speech ----------
def split_sentences(text, limit=300):
    sentences = re.split(r"(?<=[.!?।])\s+", text)
    out, cur = [], ""
    for s in sentences:
        if len(cur) + len(s) < limit:
            cur += " " + s
        else:
            if cur.strip():
                out.append(cur.strip())
            cur = s
    if cur.strip():
        out.append(cur.strip())
    return out

def play_wav(path):
    fs, data = wav_read(path)
    sd.play(data, fs)
    sd.wait()

def speak(text, lang="en"):
    voice, code = VOICES[lang]
    for piece in split_sentences(text):
        tts.synthesize(piece, voice=voice, model="timbre-v2.5",
                       language=code, output_file="reply.wav")
        play_wav("reply.wav")

def beep():
    fs = 16000
    t = np.linspace(0, 0.25, int(fs * 0.25), False)
    tone = (np.sin(2 * np.pi * 880 * t) * 12000).astype("int16")
    write("beep.wav", fs, tone)
    play_wav("beep.wav")

def listen(max_seconds=15, fs=16000):
    block = int(0.2 * fs)
    frames, started, silent = [], False, 0
    with sd.InputStream(samplerate=fs, channels=1, dtype="int16") as stream:
        for _ in range(int(max_seconds / 0.2)):
            data, _ = stream.read(block)
            frames.append(data)
            if np.abs(data).max() > SILENCE_THRESHOLD:
                started, silent = True, 0
            elif started:
                silent += 1
            if started and silent >= 6:
                break
    if not started:
        return None
    write("question.wav", fs, np.concatenate(frames))
    en = stt.transcribe("question.wav", language_code="en-IN")["transcript"].strip()
    hi = stt.transcribe("question.wav", language_code="hi-IN")["transcript"].strip()
    if not en and not hi:
        return None
    return en, hi

# ---------- repeat in either language ----------
def get_version(target):
    if LAST[target]:
        return LAST[target]
    other = "en" if target == "hi" else "hi"
    if not LAST[other]:
        return ""
    LAST[target] = translate(LAST[other], target)
    return LAST[target]

def repeat_answer(target=None):
    target = target or LAST["lang"]
    text = get_version(target)
    if text:
        speak(text, target)
    else:
        speak(MSG["en"]["no_repeat"], "en")

# ---------- main loop ----------
def main():
    chunks = load_chunks()
    if not chunks:
        print("Put .txt or .pdf files in the 'books' folder first.")
        return
    toks, idf = build_index(chunks)
    print("SPACE = ask | R = repeat | H = repeat in Hindi | E = repeat in English | Q = quit")
    speak("Ready. Press space, wait for the beep, then ask your question in English or Hindi. "
          "Press R to repeat, H to hear the last answer in Hindi, or Q to quit.")
    speak("आप हिंदी में भी सवाल पूछ सकते हैं।", "hi")

    while True:
        key = msvcrt.getwch().lower()
        try:
            if key == "q":
                speak("Goodbye.")
                break
            if key == "r":
                repeat_answer(None)
                continue
            if key == "h":
                repeat_answer("hi")
                continue
            if key == "e":
                repeat_answer("en")
                continue
            if key != " ":
                continue

            beep()
            heard = listen()
            if not heard:
                speak(MSG["en"]["nothing_heard"], "en")
                continue
            en, hi = heard
            print("English recognizer:", en)
            print("Hindi recognizer:  ", hi)

            cmd = detect_command(en, hi)
            if cmd:
                repeat_answer(None if cmd == "same" else cmd)
                continue

            lang = detect_lang(en, hi)
            if lang == "hi":
                q = hi
            else:
                q = en
                for wrong, right in CORRECTIONS.items():
                    q = re.sub(rf"\b{wrong}\b", right, q, flags=re.IGNORECASE)
            print(f"You asked ({lang}):", q)

            search_text = q
            if lang == "hi":
                try:
                    english = translate_query(q)
                    print("Translated:", english)
                    search_text = q + " " + english
                except Exception as e:
                    print("Translation failed:", e)

            passages = search(search_text, chunks, toks, idf)
            out_lang = lang
            if not passages:
                answer = MSG[lang]["not_found"]
            else:
                try:
                    answer = ask_llm(q, passages, lang)
                except Exception as e:
                    print("LLM failed, reading raw passage:", e)
                    answer = passages[0][1]
                    out_lang = "en"

            print("Answer:", answer)
            LAST["en"] = answer if out_lang == "en" else ""
            LAST["hi"] = answer if out_lang == "hi" else ""
            LAST["lang"] = out_lang
            speak(answer, out_lang)
        except Exception as e:
            print("Error:", e)
            speak(MSG["en"]["error"], "en")

main()