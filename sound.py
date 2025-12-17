import sounddevice as sd
import numpy as np
import threading
import time

# Global variables
sample_rate = 48000
audio_device = 1  # Stealth 500P headphones
current_frequency = 440  # Hz
current_volume = 0.3  # 0.0 to 1.0
is_playing = False
stream = None
phase = 0.0  # To maintain phase continuity (in radians)

def init():
    """Initialize the audio system"""
    global audio_device
    
    # Set default device
    sd.default.device = audio_device
    
    print(f"Audio initialized on device {audio_device}")
    print(f"Sample rate: {sample_rate} Hz")
    

def beep(frequency=440, duration=1.0, volume=0.3):
    """
    Play a beep tone
    
    Args:
        frequency: Frequency in Hz (default 440)
        duration: Duration in seconds (default 1.0)
        volume: Volume from 0.0 to 1.0 (default 0.3)
    """
    # Generate sine wave
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    sine_wave = volume * np.sin(2 * np.pi * frequency * t)
    
    # Play and wait for completion
    sd.play(sine_wave, sample_rate)
    sd.wait()


def set_frequency(freq):
    """Set the current frequency for continuous playback"""
    global current_frequency
    current_frequency = freq


def set_volume(vol):
    """Set the current volume (0.0 to 1.0)"""
    global current_volume
    current_volume = max(0.0, min(1.0, vol))


def start_tone():
    """Start continuous tone playback"""
    global is_playing, stream, phase
    
    if is_playing:
        return
    
    is_playing = True
    phase = 0.0  # Use float for precise phase tracking
    
    def callback(outdata, frames, time_info, status):
        global phase, current_frequency, current_volume
        
        if status:
            print(status)
        
        # Generate time array
        t = np.arange(frames) / sample_rate
        
        # Generate sine wave with current frequency
        # Phase is in radians and accumulates across all frames
        sine = current_volume * np.sin(2 * np.pi * current_frequency * t + phase)
        
        outdata[:, 0] = sine
        
        # Update phase for next callback, keeping it wrapped to avoid overflow
        # This maintains phase continuity even when frequency changes
        phase = (phase + 2 * np.pi * current_frequency * frames / sample_rate) % (2 * np.pi)
    
    stream = sd.OutputStream(
        samplerate=sample_rate,
        channels=1,
        callback=callback,
        blocksize=512
    )
    stream.start()
    print("Tone started")


def stop_tone():
    """Stop continuous tone playback"""
    global is_playing, stream, phase
    
    if not is_playing:
        return
    
    is_playing = False
    
    if stream:
        stream.stop()
        stream.close()
        stream = None
    
    phase = 0.0
    print("Tone stopped")


def cleanup():
    """Clean up audio resources"""
    stop_tone()
    print("Audio cleanup complete")


def soundscape(signal_strength, signal_shape_ratio):
    """
    Update audio based on metal detector signal
    
    Args:
        signal_strength: total signal magnitude (0 = no target, higher = stronger)
        signal_shape_ratio: not used in this version
    
    Audio mapping:
        - Volume: proportional to signal_strength
        - Frequency: proportional to signal_strength (higher signal = higher pitch)
    """
    global current_frequency, current_volume
    
    # Map signal strength to volume (0.05 to 0.7 for better sensitivity)
    max_expected_strength = 100  # Lowered for more sensitivity
    min_volume = 0.05   # Minimum volume instead of 0
    max_volume = 0.7    # Maximum volume instead of 0.5

    strength_ratio = min(1.0, signal_strength / max_expected_strength)
    current_volume = min_volume + (max_volume - min_volume) * strength_ratio
    
    # Map signal strength to frequency
    min_freq = 400   # Frequency at zero signal
    max_freq = 1000  # Frequency at max signal
    
    strength_ratio = min(1.0, signal_strength / max_expected_strength)
    current_frequency = min_freq + (max_freq - min_freq) * strength_ratio
    
    print(f"Strength: {signal_strength:.0f}, Freq: {current_frequency:.0f} Hz, Vol: {current_volume:.3f}")
    
    # Ensure tone is playing
    if not is_playing:
        start_tone()
