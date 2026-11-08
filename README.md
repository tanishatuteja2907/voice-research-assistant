# Voice Research Assistant for Visually Impaired People

Ask questions about any book or document by voice, in English or Hindi, and hear the answer spoken back.

- One-page pitch: [PITCH.md](PITCH.md)
- Demo video: PASTE-YOUR-VIDEO-LINK-HERE

## How it works
Mic -> Gnani STT (Prisma) -> search over document text -> Gemini answer -> Gnani TTS (Timbre) -> speaker

Ask in English or Hindi, and the answer comes back in the same language. Press H to hear the last answer in Hindi, or E for English.

## Setup (Windows)
1. `python -m venv venv`, then `venv\Scripts\activate`
2. `pip install -r requirements.txt`
3. Create a `.env` file with `GNANI_API_KEY=...` and `GEMINI_API_KEY=...`
4. Put your own `.txt` or `.pdf` files in a `books` folder
5. `python assistant.py`

## Controls
SPACE = ask (wait for the beep) | R = repeat | H = repeat in Hindi | E = repeat in English | Q = quit

## Built with
Gnani Vachana speech AI (speech-to-text and text-to-speech) and Google Gemini.