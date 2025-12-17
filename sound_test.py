import sounddevice as sd
import numpy as np

sd.default.device = 1  # Your Stealth 500P headphones

# Play a 1 second beep
fs = 48000
duration = 1
t = np.linspace(0, duration, int(fs * duration))
sine = np.sin(2 * np.pi * 440 * t)
sd.play(sine, fs)
sd.wait()
