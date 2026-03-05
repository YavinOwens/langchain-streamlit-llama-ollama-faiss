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
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found"
    exit 1
fi

# Check if requirements.txt has changed since last installation
if [ -f ".deps_installed" ] && [ -f "requirements.txt" ]; then
    if [ "requirements.txt" -nt ".deps_installed" ]; then
        echo "📝 Requirements.txt has changed, reinstalling dependencies..."
        rm -f .deps_installed
    fi
fi

# Install dependencies if needed
if [ ! -f ".deps_installed" ]; then
    echo "📥 Installing dependencies..."
    if pip install -r requirements.txt; then
        touch .deps_installed
        echo "✅ Dependencies installed successfully"
    else
        echo "❌ Failed to install dependencies"
        exit 1
    fi
else
    echo "✅ Dependencies already installed"
fi

# Run Streamlit with optimized settings
echo "🦙 Starting Streamlit app..."

# Check if streamlit is available
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not found. Installing..."
    pip install streamlit
fi

# Run the app
if streamlit run app.py --server.port=8501 --server.address=localhost; then
    echo "🎉 Application started successfully!"
else
    echo "❌ Failed to start application"
    exit 1
fi
