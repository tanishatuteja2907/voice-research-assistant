from dotenv import load_dotenv
load_dotenv()

from gnani.tts import GnaniTTSClient

client = GnaniTTSClient()

audio = client.synthesize(
    "नमस्ते, आप कैसे हैं?",
    voice="Nalini",
    model="timbre-v2.5",
    language="hi-IN",
    output_file="output.wav",
)

print("Done,", len(audio), "bytes saved to output.wav")