#!/bin/bash
cd /home/zfz/watermark-service
source venv/bin/activate

# Kill any existing uvicorn
pkill -f 'uvicorn app.main' 2>/dev/null

# Start the service
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8900 --workers 1 > /home/zfz/watermark-service/service.log 2>&1 &
echo PID=$!
sleep 2
tail -20 /home/zfz/watermark-service/service.log
