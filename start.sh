#!/bin/bash

# Activate virtual environment
source .venv/bin/activate

# Start llama.cpp server
python -m llama_cpp.server \
    --model models/Phi-3-mini-4k-instruct-q4.gguf \
    --host 0.0.0.0 \
    --port 8080 \
    --n_ctx 4096
