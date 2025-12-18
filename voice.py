#!/usr/bin/env python3
"""
Voice module for WOMBAT PiPi metal detector.
Uses espeak-ng directly for reliable female voice.
"""

import subprocess
import threading
import queue
import time
import sys

class VoiceEngine:
    """Thread-safe voice engine using espeak-ng directly."""
    
    def __init__(self, rate=160, pitch=70, voice='en+f3', volume=100):
        """Initialize the voice engine.
        
        Args:
            rate: Speech rate (words per minute), default 160
            pitch: Pitch (0-99), default 70 (higher = more feminine)
            voice: Voice variant, default 'en+f3' (English female 3)
            volume: Volume (0-200), default 100
        """
        self.rate = rate
        self.pitch = pitch
        self.voice = voice
        self.volume = volume
        self.queue = queue.Queue()
        self.running = False
        self.worker_thread = None
        
    def _speak_direct(self, text):
        """Call espeak-ng directly with female voice settings."""
        try:
            cmd = [
                'espeak-ng',
                '-v', self.voice,      # Voice variant
                '-p', str(self.pitch), # Pitch (50-99, higher = more feminine)
                '-s', str(self.rate),  # Speed in words per minute
                '-a', str(self.volume),# Amplitude/volume (0-200)
                '-g', '8',             # Word gap (pause between words)
                text
            ]
            
            # Run espeak-ng (blocks until speech completes)
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"[Voice] espeak-ng error: {e}")
            return False
        except FileNotFoundError:
            print("[Voice] espeak-ng not found. Install with: sudo apt install espeak-ng")
            return False
        except Exception as e:
            print(f"[Voice] Unexpected error: {e}")
            return False
    
    def _worker(self):
        """Background worker that processes speech queue."""
        while self.running:
            try:
                # Get text from queue with timeout
                text = self.queue.get(timeout=0.5)
                
                if text is None:  # Shutdown signal
                    break
                    
                print(f"[Voice] Speaking: {text}")
                self._speak_direct(text)
                    
                self.queue.task_done()
                
            except queue.Empty:
                continue  # No messages, keep waiting
            except Exception as e:
                print(f"[Voice] Error in worker: {e}")
                time.sleep(0.1)
    
    def start(self):
        """Start the voice engine worker thread."""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker, daemon=True)
            self.worker_thread.start()
            print(f"[Voice] Engine started (voice: {self.voice}, pitch: {self.pitch})")
    
    def stop(self):
        """Stop the voice engine."""
        if self.running:
            self.running = False
            self.queue.put(None)  # Signal shutdown
            if self.worker_thread:
                self.worker_thread.join(timeout=2.0)
            print("[Voice] Engine stopped")
    
    def say(self, text):
        """Queue text for speaking (non-blocking).
        
        Args:
            text: String to speak
        """
        if self.running and text:
            self.queue.put(text)
            return True
        else:
            print(f"[Voice] Not running, cannot speak: {text}")
            return False
    
    def update_voice(self, voice=None, pitch=None, rate=None, volume=None):
        """Update voice settings on the fly."""
        if voice: self.voice = voice
        if pitch: self.pitch = pitch
        if rate: self.rate = rate
        if volume: self.volume = volume
        print(f"[Voice] Updated settings: voice={self.voice}, pitch={self.pitch}, rate={self.rate}")

# Global instance for easy import
_voice_engine = None

def init(rate=160, pitch=70, voice='en+f3', volume=100):
    """Initialize the global voice engine.
    
    Args:
        rate: Speech rate (words per minute)
        pitch: Pitch (0-99), higher = more feminine
        voice: Voice variant (e.g., 'en+f2', 'en-us+f3')
        volume: Volume (0-200)
    """
    global _voice_engine
    if _voice_engine is None:
        _voice_engine = VoiceEngine(rate=rate, pitch=pitch, voice=voice, volume=volume)
        _voice_engine.start()
    return _voice_engine

def say(text):
    """Main interface: speak text (non-blocking).
    
    Args:
        text: String to speak
    """
    global _voice_engine
    if _voice_engine is None:
        # Auto-initialize with female voice defaults
        init()
    return _voice_engine.say(text)

def update_settings(voice=None, pitch=None, rate=None, volume=None):
    """Update voice settings."""
    global _voice_engine
    if _voice_engine:
        _voice_engine.update_voice(voice, pitch, rate, volume)

def stop():
    """Stop the voice engine."""
    global _voice_engine
    if _voice_engine:
        _voice_engine.stop()
        _voice_engine = None

def test_voice_variants():
    """Test different female voice options."""
    variants = [
        ('en+f2', 65, 'Female voice 2'),
        ('en+f3', 70, 'Female voice 3'),
        ('en+f4', 75, 'Female voice 4'),
        ('en-us+f3', 72, 'US English female'),
    ]
    
    for voice, pitch, desc in variants:
        print(f"\n[Test] {desc} (voice={voice}, pitch={pitch})")
        update_settings(voice=voice, pitch=pitch)
        say(f"This is {desc}")
        time.sleep(2.5)

def main():
    """Standalone test function."""
    print("=== Voice Module Test (espeak-ng direct) ===")
    print("Press Ctrl+C to exit\n")
    
    try:
        # Initialize with female voice
        init(rate=150, pitch=72, voice='en+f3')
        time.sleep(0.5)  # Let engine start
        
        # Test
        say("Voice module initialized with female voice.")
        time.sleep(3)
        
        # Test different variants
        print("\nTesting voice variants...")
        test_voice_variants()
        
        # Interactive test
        print("\n\nInteractive test. Type messages to speak (or 'quit'):")
        while True:
            user_input = input(">> ").strip()
            if not user_input:
                continue
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            say(user_input)
            
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    finally:
        stop()
        print("Voice engine stopped")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
