#!/usr/bin/env bash
set -Eeuo pipefail

# Kill all children on exit
trap 'jobs -p | xargs -r kill 2>/dev/null' EXIT

# Helper: wait until port $1 is LISTENING
wait_for_port() {
  local port=$1
  echo "Waiting for port $port to listen..."
  until ss -ltn "( sport = :$port )" | grep -q LISTEN; do
    sleep 0.1
  done
  echo "Port $port is now listening."
}

# 1) Start merger node (Node 4)
echo "Starting merger (Node 4)..."
python3 ./merger_node/run_merger.py \
  --transcription-port 8003 \
  --diarization-port 8004 \
  --diarization-buffer-size 120 \
  --maximum-diarization-delay 0 &
merge_pid=$!

# 2) Wait until merger is ready on 8003 & 8004
wait_for_port 8003
wait_for_port 8004

# 3) Start Whisper server (Node 2) → pipe its stdout into merger’s transcription port (8003)
echo "Starting Whisper server (Node 2)..."
python3 ./simulstreaming_node/simulstreaming_whisper_server.py \
  --host localhost --port 8001 \
  --min-chunk-size 1.0 --task transcribe \
  --vac --vac-chunk-size 0.5 --log-level CRITICAL \
  --language auto \
| nc localhost 8003 &
whisper_pipe_pid=$!

# 4) Start diarization server (Node 3) → pipe its stdout into merger’s diarization port (8004)
echo "Starting diarization server (Node 3)..."
python3 ./diart_node/run_diart.py \
  --sample-rate 16000 --chunk-duration 0.1 \
  --host localhost --port 8002 \
| nc localhost 8004 &
diart_pipe_pid=$!

# 5) Wait until Whisper (8001) and Diart (8002) are listening
wait_for_port 8001
wait_for_port 8002

# 6) Finally start the netcat listener (Node 1) and duplicate its output to 8001 & 8002
echo "Starting router (Node 1) and teeing → 8001 & 8002..."
#  - `nc -lk 8000` listens forever, its stdout is fed to tee
#  - tee duplicates into two process‐substitutions, each piping into nc → target port
#  - the main tee stdout goes to /dev/null
tee >(nc localhost 8001) >(nc localhost 8002) >/dev/null < <(nc -lk 8000) &
router_pid=$!

# 7) Wait on merger so you see its output (all other nodes are backgrounded)
wait "$merge_pid"