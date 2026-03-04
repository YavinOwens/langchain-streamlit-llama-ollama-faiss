#!/bin/bash

# Optimized run script for Mac M2 with 8GB RAM
echo "🚀 Starting Local Llama Chat (Mac M2 Optimized)"

# Set environment variables for optimization
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_LOAD_TIMEOUT=5m
export OLLAMA_GPU_MAX_ALLOCATION=0.8  # Use 80% of GPU memory
export OLLAMA_METAL=1  # Force Metal usage
export PYTHONPATH="$PWD"

# Check if Ollama is running
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "⚠️  Ollama is not running. Starting Ollama..."
    ollama serve &
    sleep 3
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f ".deps_installed" ]; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
    touch .deps_installed
fi

# Run Streamlit with optimized settings
echo "🦙 Starting Streamlit app..."
streamlit run app.py --server.port=8501 --server.address=localhost
