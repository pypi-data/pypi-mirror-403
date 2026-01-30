#!/bin/bash
# Startup script for running headless-shell and uvicorn together
# Handles graceful shutdown via SIGTERM from Cloud Run

set -e

# Start headless-shell in background
# --no-sandbox is required when running as root in containers
# --disable-gpu since we don't have GPU in Cloud Run
# --remote-debugging-address binds to localhost only for security
echo "Starting headless-shell on port ${CHROME_PORT:-9222}..."
/headless-shell/headless-shell \
    --no-sandbox \
    --disable-gpu \
    --disable-software-rasterizer \
    --disable-dev-shm-usage \
    --remote-debugging-address=${CHROME_HOST:-127.0.0.1} \
    --remote-debugging-port=${CHROME_PORT:-9222} \
    &
CHROME_PID=$!

# Wait for Chrome to be ready
echo "Waiting for Chrome to be ready..."
for i in {1..30}; do
    if curl -s "http://${CHROME_HOST:-127.0.0.1}:${CHROME_PORT:-9222}/json/version" > /dev/null 2>&1; then
        echo "Chrome is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "ERROR: Chrome failed to start within 30 seconds"
        exit 1
    fi
    sleep 1
done

# Handle graceful shutdown
cleanup() {
    echo "Received shutdown signal, stopping services..."
    # Kill uvicorn first (it handles SIGTERM gracefully)
    if [ ! -z "$UVICORN_PID" ]; then
        kill -TERM $UVICORN_PID 2>/dev/null || true
        wait $UVICORN_PID 2>/dev/null || true
    fi
    # Then stop Chrome
    if [ ! -z "$CHROME_PID" ]; then
        kill -TERM $CHROME_PID 2>/dev/null || true
        wait $CHROME_PID 2>/dev/null || true
    fi
    echo "Shutdown complete"
    exit 0
}
trap cleanup SIGTERM SIGINT

# Start uvicorn in foreground (use Python module)
echo "Starting uvicorn on port ${PORT:-8080}..."
.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} &
UVICORN_PID=$!

# Wait for either process to exit
wait -n $CHROME_PID $UVICORN_PID

# If we get here, one of the processes died unexpectedly
echo "A process exited unexpectedly, shutting down..."
cleanup
