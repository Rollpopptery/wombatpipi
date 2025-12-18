import asyncio
import websockets
import json
import numpy as np
import serial_reader
import settings
import functions
import sound
import copy

# Initialize
sound.init()

# Initialize serial
serial_reader.init()
serial_reader.start_reading()

async def stream_data(websocket):
    """Stream data and handle incoming commands"""
    print(f"Client connected: {websocket.remote_address}")
    
    try:
        # Send initial tau value
        await websocket.send(json.dumps({
            'type': 'settings',
            'tau': settings.settings.tau
        }))
        
        async def send_data():
            while True:
                latest = serial_reader.get_latest()
                avg = serial_reader.get_average()
                
                if latest and avg:
                    normalized = np.array(avg['signal']) - np.array(avg['values'])
                    
                    # Extract signal features for soundscape
                    features = copy.copy(functions.current_features)  # Shallow copy
                    
                                        
                    # Calculate shape ratio
                    #if features['second_half_sum'] > 0:
                        #ratio = features['first_half_sum'] / features['second_half_sum']
                    #else:
                        #ratio = 1.0
                    ratio = features['ratio']
                    
                    # Update soundscape based on signal
                    #sound.soundscape(features['total_sum'], ratio)
                    
                    data = {
                        'type': 'data',
                        'times': latest['times_us'],
                        'values': normalized.tolist(),
                        'timestamp': latest['timestamp'],
                        'features': {
                            'total_sum': features['total_sum'],
                            'first_half_sum': features['first_half_sum'],
                            'second_half_sum': features['second_half_sum'],
                            'diff': features['diff'],
                            'cumulative_total':features['cumulative_total'],
                            'ratio': ratio
                        }
                    }
                    
                    await websocket.send(json.dumps(data))
                
                await asyncio.sleep(0.1)
        
        async def receive_commands():
            async for message in websocket:
                try:
                    cmd = json.loads(message)
                    if cmd.get('type') == 'set_tau':
                        settings.settings.tau = cmd['tau']
                        print(f"TAU updated to: {settings.settings.tau} µs")
                        await websocket.send(json.dumps({
                            'type': 'settings',
                            'tau': settings.settings.tau
                        }))
                except Exception as e:
                    print(f"Error processing command: {e}")
        
        await asyncio.gather(send_data(), receive_commands())
        
    except websockets.exceptions.ConnectionClosed:
        print(f"Client disconnected: {websocket.remote_address}")
        # Stop sound when client disconnects
        sound.stop_tone()
        
async def main():
    async with websockets.serve(stream_data, "0.0.0.0", 8765):
        print("WebSocket server running on ws://0.0.0.0:8765")
        print("Streaming metal detector data at 10Hz")
        print("Audio soundscape enabled")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
