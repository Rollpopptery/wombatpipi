#!/bin/bash
# Start both servers


cd /home/pi/wombat
source /home/pi/venv/bin/activate  # ABSOLUTE PATH
python websocket_server.py &
python3 -m http.server 8080 &
wait

