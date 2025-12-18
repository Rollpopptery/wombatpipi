#!/usr/bin/env python3
"""
WAV Player for number sounds (00-99).
Plays WAV files in sequence with precise timing.
"""

import pygame
import threading
import queue
import os
import subprocess


IS_PLAYING = False

def is_playing():
	return IS_PLAYING


class WavPlayer:
    """Plays number WAV files with precise timing using pygame channels."""
    
    def __init__(self, wav_path="wavs"):
        self.wav_path = wav_path
        self.queue = queue.Queue()
        self.running = False
        self.worker_thread = None
        
       
    
    def _load_sounds(self):
        """Load all WAV files (0-9) into memory."""
        for i in range(10):
            filepath = os.path.join(self.wav_path, f"{i}.wav")
            if os.path.exists(filepath):
                try:
                    self.sounds[str(i)] = pygame.mixer.Sound(filepath)
                except Exception as e:
                    print(f"[WAV] Failed to load {filepath}: {e}")
            else:
                print(f"[WAV] Warning: Missing {filepath}")
    
    def _wait_for_channel(self, channel):
        """Wait efficiently for a channel to finish playing."""
        if channel:
            # Busy-wait with tiny sleeps (more efficient than pygame.time.wait)
            while channel.get_busy():
                pygame.time.wait(10)  # 10ms checks
    
   

    def _say_number(self, number_str):
        global IS_PLAYING        
    
        IS_PLAYING = True
    
        # Play each digit using aplay (blocks)
        for digit in number_str:
            wav_file = f"{self.wav_path}/{digit}.wav"
            subprocess.run([
                "aplay", "-q",
                "-D", "default",  # Use dmix device
                wav_file
            ])
    
        IS_PLAYING = False
        # Tone continues automatically via dmix
  
    
    def _worker(self):
        """Background worker that processes number queue."""
        while self.running:
            try:
                number_str = self.queue.get(timeout=0.5)
                if number_str is None:
                    break
                self._say_number(number_str)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[WAV] Error: {e}")
    
    def start(self):
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker, daemon=True)
            self.worker_thread.start()
    
    def stop(self):
        if self.running:
            self.running = False
            self.queue.put(None)
            if self.worker_thread:
                self.worker_thread.join(timeout=2.0)
            pygame.mixer.quit()
    
    def say_number(self, number):
        """Queue a number (00-99) to play."""
        if not self.running:
            return False
        
        num_str = str(number).zfill(2)
        if len(num_str) != 2 or not num_str.isdigit():
            return False
        
        self.queue.put(num_str)
        return True

# Global instance
_player = None

def init(wav_path="wavs"):
    global _player
    if _player is None:
        _player = WavPlayer(wav_path)
        _player.start()
    return _player

def say(number):
    global _player
    if _player is None:
        init()
    return _player.say_number(number)

def stop():
    global _player
    if _player:
        _player.stop()
        _player = None

def test_blocking():
    """Test that plays numbers and waits for each."""
    init()
    
    for i in range(21):
        print(f"Playing {i:02d}")
        # Direct blocking play (bypass queue)
        _player._say_number(f"{i:02d}")
    
    print("Test complete")
    
if __name__ == "__main__":
    test_blocking()
    import time
    time.sleep(5)  # Wait for playback
    stop()
