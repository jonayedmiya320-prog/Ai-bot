#!/bin/bash
# Ubuntu/Debian VPS এর জন্য। চালান: bash install.sh
set -e
sudo apt update -y
sudo apt install -y python3 python3-pip python3-venv curl

# Ollama ইনস্টল
if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
fi

# Python এনভায়রনমেন্ট
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# ডিফল্ট মডেল ডাউনলোড (পরে প্যানেল থেকেও অন্য মডেল নামানো যাবে)
ollama pull gemma3:4b

echo ""
echo "ইনস্টল শেষ। এখন config.json এ শুধু bot_token বসান।"
echo "তারপর চালান: ./venv/bin/python main.py"
