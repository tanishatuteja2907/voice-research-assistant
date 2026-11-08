# Voice Research Assistant for Visually Impaired users

Ask questions about a textbook by voice, in English or Hindi, and hear the answer spoken back.

## The problem
A textbook is hard to skim or search without sight. This assistant lets a user simply ask a question and listen to the answer.

## How it works
Mic -> Gnani STT (Prisma) -> search over book text -> Gemini answer -> Gnani TTS (Timbre) -> speaker

- Ask in English or Hindi, and the answer comes back in the same language.
- Press H to hear the last answer in Hindi, or E to hear it in English.

## Setup (Windows)
1. `python -m venv venv`, then `venv\Scripts\activate`
2. `pip install -r requirements.txt`
3. Create a `.env` file with: