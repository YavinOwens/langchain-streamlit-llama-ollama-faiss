#!/bin/bash

# PubMed Search Launcher
# This script launches the PubMed search interface

echo "🔬 Starting PubMed Search Interface..."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: Virtual environment not detected"
    echo "💡 Consider activating venv first: source venv/bin/activate"
fi

# Check if required packages are installed
python -c "import streamlit, pandas, plotly, langchain_community.utilities.pubmed" 2>/dev/null
if [[ $? -ne 0 ]]; then
    echo "📦 Installing required packages..."
    pip install streamlit pandas plotly langchain-community xmltodict
fi

# Set port (default 8503, or use provided argument)
PORT=${1:-8503}

echo "🚀 Launching PubMed Search on port $PORT..."
echo "🌐 Access at: http://localhost:$PORT"
echo "⏹️  Press Ctrl+C to stop"

# Run the PubMed search app
streamlit run pubmed_search.py --server.port=$PORT --server.headless=false
