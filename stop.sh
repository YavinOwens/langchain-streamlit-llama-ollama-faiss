#!/bin/bash

# Stop script for Local Llama Chat application
echo "Stopping Local Llama Chat application..."

# Stop Streamlit application
if pgrep -f "streamlit run app.py" > /dev/null; then
    echo "Stopping Streamlit application..."
    pkill -f "streamlit run app.py"
    echo "Streamlit application stopped"
else
    echo "Streamlit application is not running"
fi

# Stop Ollama service
if pgrep -f "ollama serve" > /dev/null; then
    echo "Stopping Ollama service..."
    pkill -f "ollama serve"
    echo "Ollama service stopped"
else
    echo "Ollama service is not running"
fi

# Clean up any remaining processes (but NOT the virtual environment)
if pgrep -f "ollama" > /dev/null; then
    echo "Cleaning up remaining Ollama processes..."
    pkill -f "ollama"
fi

echo "All services stopped successfully"
echo "Virtual environment and dependencies preserved"
