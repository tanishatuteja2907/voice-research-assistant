# Voice Research Assistant for Visually Impaired People

## Problem
Printed books, forms and documents are hard to skim or search without sight, and most tools assume a screen and English. Many people end up depending on someone else to read for them.

## Solution
A voice-first assistant. Ask a question out loud, in English or Hindi, and hear the answer spoken back, taken from the books and documents you give it. The answer comes in the language you spoke, and you can ask to hear it again in Hindi or English.

## How it works
Mic -> Gnani Prisma (speech-to-text) -> search over the document text -> Gemini writes a short answer from the matching passages -> Gnani Timbre (text-to-speech) -> speaker

## Why Gnani
Gnani's speech models recognise Indian English and Hindi and speak back in natural voices. That makes the experience usable for Indian users, which English-only tools are not.

## Current status
Working prototype: voice Q&A in two languages over textbooks, stories and other documents, with repeat and language-switch controls.

## Next steps
- A one-button web and phone version that works with screen readers
- More Indian languages
- Reading scanned pages with OCR
- Meaning-based search for better answers from large documents
- Page references and read-aloud of longer sections