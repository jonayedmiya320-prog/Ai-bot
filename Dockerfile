FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl zstd ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Ollama ইনস্টল
RUN curl -fsSL https://ollama.com/install.sh | sh

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x start.sh

ENV DATA_DIR=/data
ENV OLLAMA_MODELS=/data/models
CMD ["./start.sh"]
