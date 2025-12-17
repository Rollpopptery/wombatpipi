import serial
import numpy as np
import threading
import time
from collections import deque
from functions import AdaptiveMovingAverage
import functions
import sound  # Add sound import

CURVE_SAMPLE_SIZE = 25
TIME_BUFFER_SIZE = 100

# Global variables
serial_port = None
serial_device = '/dev/ttyACM0'  # Default USB serial device (change to match your device)
baud_rate = 230400
is_reading = False
read_thread = None

# Data storage
data_buffer = deque(maxlen=TIME_BUFFER_SIZE)  # Store last 100 discharge curves (10 seconds at 10Hz)
latest_curve = None
sample_interval_us = 3  # microseconds between samples
running_sum = np.zeros(CURVE_SAMPLE_SIZE)  # Sum of last 100 curves for each point

# adaptive moving average
long_average_curve = AdaptiveMovingAverage(CURVE_SAMPLE_SIZE, alpha_slow=0.03, alpha_fast=0.1)
fast_average_curve = AdaptiveMovingAverage(CURVE_SAMPLE_SIZE, alpha_slow=0.3, alpha_fast=0.3)

# Sound control
enable_sound = True  # Flag to enable/disable sound updates

def set_sound_enabled(enabled):
    """Enable or disable real-time sound updates"""
    global enable_sound
    enable_sound = enabled
    if not enabled:
        # Stop sound when disabled
        try:
            sound.stop_tone()
        except:
            pass
    print(f"Sound updates {'enabled' if enabled else 'disabled'}")

def get_compensation_factors():
    """Calculate compensation factors based on current tau setting"""
    import settings
    tau = settings.settings.tau
    return np.exp(np.arange(CURVE_SAMPLE_SIZE) * sample_interval_us / tau)

def init(device=None, baud=230400):
    """
    Initialize the serial port
    
    Args:
        device: Serial device path (default uses serial_device global)
        baud: Baud rate (default 230400)
    """
    global serial_port, serial_device, baud_rate
    
    # Use provided device or fall back to global default
    if device is None:
        device = serial_device
    else:
        serial_device = device
        
    baud_rate = baud
    
    try:
        serial_port = serial.Serial(
            port=device,
            baudrate=baud,
            timeout=1,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )
        print(f"Serial port initialized: {device} at {baud} baud")
        return True
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        return False

def start_reading():
    """Start reading from serial port in background thread"""
    global is_reading, read_thread
    
    if is_reading:
        print("Already reading")
        return
    
    if serial_port is None or not serial_port.is_open:
        print("Serial port not initialized")
        return False
    
    is_reading = True
    read_thread = threading.Thread(target=_read_loop, daemon=True)
    read_thread.start()
    print("Serial reading started")
    return True

def stop_reading():
    """Stop reading from serial port"""
    global is_reading
    
    is_reading = False
    if read_thread:
        read_thread.join(timeout=2)
    print("Serial reading stopped")

def _read_loop():
    """Background thread that continuously reads serial data"""
    global latest_curve, running_sum, long_average_curve, fast_average_curve
    
    while is_reading:
        try:
            if serial_port and serial_port.in_waiting > 0:
                # Read a line from serial
                line = serial_port.readline().decode('utf-8', errors='ignore').strip()
                
                if line:
                    # Parse CSV values - expecting CURVE_SAMPLE_SIZE values per discharge curve
                    try:
                        # Split and convert to floats, filtering empty strings
                        values = [float(x) for x in line.split(',') if x.strip()]
                        
                        if len(values) == CURVE_SAMPLE_SIZE:
                            values_array = np.array(values)
                            
                            # Apply tau compensation to flatten exponential decay
                            #   compensated = values_array * get_compensation_factors()
                            compensated = values_array
                            
                            # Update the adaptive moving averages
                            long_average_curve.update(compensated)
                            fast_average_curve.update(compensated)
                            
                            # === REAL-TIME SOUND UPDATES ===
                            if enable_sound:
                                try:
                                    # Calculate normalized signal (fast signal - long baseline)
                                    fast_signal = fast_average_curve.get_average()
                                    long_baseline = long_average_curve.get_average()
                                    normalized = fast_signal - long_baseline
                                    
                                    # Extract signal features for sound
                                    features = functions.extract_signal_features(normalized.tolist())
                                    
                                    # Calculate shape ratio
                                    if features['second_half_sum'] > 0:
                                        ratio = features['first_half_sum'] / features['second_half_sum']
                                    else:
                                        ratio = 1.0
                                    
                                    # Update sound at real data rate (~20Hz)
                                    sound.soundscape(features['first_half_sum'], ratio)
                                    
                                except Exception as e:
                                    print(f"Sound update error: {e}")
                            
                            # Valid discharge curve - store compensated values
                            curve_data = {
                                'timestamp': time.time(),
                                'values': compensated.tolist(),
                                'times_us': [i * sample_interval_us for i in range(CURVE_SAMPLE_SIZE)]
                            }
                            
                            data_buffer.append(curve_data)
                            latest_curve = curve_data
                        else:
                            # Wrong number of values - log warning
                            print(f"Warning: Expected {CURVE_SAMPLE_SIZE} values, got {len(values)}")
                        
                    except ValueError as e:
                        # Failed to parse numbers
                        print(f"Parse error: {e}")
                        
        except serial.SerialException as e:
            print(f"Serial read error: {e}")
            time.sleep(0.1)
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(0.1)

def get_latest():
    """Get the most recent discharge curve"""
    return latest_curve

def get_buffer():
    """Get all buffered data"""
    return list(data_buffer)

def get_average():
    """Get the running average of all buffered curves"""
    return {
        'values': long_average_curve.get_average(),
        'signal': fast_average_curve.get_average(),
        'times_us': [i * sample_interval_us for i in range(CURVE_SAMPLE_SIZE)]
    }

def clear_buffer():
    """Clear the data buffer"""
    global latest_curve, running_sum, long_average_curve, fast_average_curve
    data_buffer.clear()
    latest_curve = None
    running_sum.fill(0)
    long_average_curve.reset()
    fast_average_curve.reset()  # Also reset fast average

def list_serial_ports():
    """List available serial ports"""
    import serial.tools.list_ports
    ports = serial.tools.list_ports.comports()
    available = []
    for port in ports:
        available.append({
            'device': port.device,
            'description': port.description,
            'hwid': port.hwid
        })
    return available

def cleanup():
    """Clean up serial resources"""
    stop_reading()
    if serial_port and serial_port.is_open:
        serial_port.close()
    # Stop sound on cleanup
    try:
        sound.stop_tone()
    except:
        pass
    print("Serial cleanup complete")
