import sounddevice as sd
import numpy as np

fs = 16000
print("Speak normally for 5 seconds...")
a = sd.rec(5 * fs, samplerate=fs, channels=1, dtype="int16")
sd.wait()
print("Background level:", int(np.percentile(np.abs(a), 20)))
print("Peak level:", int(np.abs(a).max()))