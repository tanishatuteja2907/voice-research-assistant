import sounddevice as sd
from scipy.io.wavfile import write

fs = 16000  # 16 kHz works well
print("Recording for 7 seconds, speak now...")
audio = sd.rec(int(7 * fs), samplerate=fs, channels=1, dtype="int16")
sd.wait()
write("audio.wav", fs, audio)
print("Saved audio.wav")