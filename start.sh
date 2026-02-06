#!/bin/sh
set -e

# Start FastAPI (TalentAI API)
(
  cd backend
  uvicorn main:app --host 0.0.0.0 --port "${API_PORT:-8000}" --workers "${UVICORN_WORKERS:-2}"
) &
API_PID=$!

# Start Gradio UI (HireStream Match)
(
  cd backend/match_service
  python app_gradio.py
) &
GRADIO_PID=$!

cleanup() {
  kill "$API_PID" "$GRADIO_PID" 2>/dev/null || true
}

trap cleanup INT TERM

# Exit if any process stops unexpectedly.
while true; do
  if ! kill -0 "$API_PID" 2>/dev/null; then
    echo "FastAPI process exited"
    cleanup
    break
  fi
  if ! kill -0 "$GRADIO_PID" 2>/dev/null; then
    echo "Gradio process exited"
    cleanup
    break
  fi
  sleep 1
done

wait 2>/dev/null || true

