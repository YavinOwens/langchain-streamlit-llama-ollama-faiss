#!/bin/bash

# PubMed Research Hub Launcher
# Standalone Streamlit application for advanced biomedical literature search

echo "🔬 Launching PubMed Research Hub..."

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

# Set port (default 8504, or use provided argument)
PORT=${1:-8504}

echo "🚀 Launching PubMed Research Hub on port $PORT..."
echo "🌐 Access at: http://localhost:$PORT"
echo "⏹️  Press Ctrl+C to stop"
echo "📚 Features: PubMed search, dataframe preview, analytics, export"

# Run the PubMed Research Hub
streamlit run pubmed_app.py --server.port=$PORT --server.headless=false --browser.gatherUsageStats=false
