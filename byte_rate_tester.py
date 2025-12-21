#!/usr/bin/env python3
"""
Serial byte rate tester - measures raw incoming bytes per second
"""
import serial
import time

def measure_byte_rate(port, baudrate=1000000, duration=10):
    """
    Measure raw bytes per second from serial port
    
    Args:
        port: Serial port path (e.g., '/dev/ttyACM0')
        baudrate: Baud rate 
        duration: How long to measure in seconds
    """
    ser = serial.Serial(port, baudrate, timeout=0)
    
    print(f"Measuring byte rate on {port} for {duration} seconds...")
    print("Press Ctrl+C to stop early")
    
    total_bytes = 0
    start_time = time.time()
    last_print_time = start_time
    
    try:
        while True:
            current_time = time.time()
            
            # Read all available bytes
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                total_bytes += len(data)
            
            # Print stats every second
            if current_time - last_print_time >= 1.0:
                elapsed = current_time - start_time
                rate = total_bytes / elapsed
                print(f"Time: {elapsed:.1f}s | Total bytes: {total_bytes} | Rate: {rate:.0f} bytes/sec")
                last_print_time = current_time
            
            # Stop after duration
            if current_time - start_time >= duration:
                break
                
    except KeyboardInterrupt:
        print("\nStopped by user")
    
    finally:
        ser.close()
        
        # Final stats
        total_time = time.time() - start_time
        final_rate = total_bytes / total_time
        print(f"\n--- Final Results ---")
        print(f"Duration: {total_time:.2f} seconds")
        print(f"Total bytes: {total_bytes}")
        print(f"Average rate: {final_rate:.0f} bytes/sec")
        print(f"Expected at 400 fps: {400 * 52} bytes/sec")
        print(f"Efficiency: {(final_rate / (400 * 52)) * 100:.1f}%")

if __name__ == "__main__":
    # Change these as needed
    PORT = "/dev/ttyACM0"
    BAUDRATE = 1000000
    DURATION = 10  # seconds
    
    measure_byte_rate(PORT, BAUDRATE, DURATION)
