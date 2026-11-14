#!/bin/bash
mkdir -p /data/models /data/users

# OLLAMA_URL সেট থাকলে (পরে VPS কিনলে) এখানে আর Ollama চালু হবে না
if [ -z "$OLLAMA_URL" ]; then
  ollama serve > /tmp/ollama.log 2>&1 &
  for i in $(seq 1 40); do
    curl -s http://127.0.0.1:11434/api/tags >/dev/null && break
    sleep 1
  done
fi

exec python main.py
