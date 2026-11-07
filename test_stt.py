from dotenv import load_dotenv
load_dotenv()

from gnani.stt import GnaniSTTClient

client = GnaniSTTClient()

result = client.transcribe("audio.wav", language_code="hi-IN")
print(result)