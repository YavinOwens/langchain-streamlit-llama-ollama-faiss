# 🦙 Local Llama Chat with Document Intelligence

GenAI companion for document processing, Q&A. fun for first time genai developers/researchers, students, and professionals who want to chat with their documents.

## 🎨 Features at a Glance

| Feature                      | Description                                | 
| ---------------------------- | ------------------------------------------ | 
| **📄 Document Q&A**    | Chat with PDFs, Word, PowerPoint, images   | 
| **🌐 Web Integration** | Scrape websites and YouTube videos         | 
| **🦙 Local LLM**       | Ollama-powered conversations               | 
| **🔧 Smart Tools**     | Search, math, weather, analytics           | 
| **📊 Analytics**       | Track response quality and improve         | 
| **🗃️ Database**      | PostgreSQL integration for structured data | 

1. **document loaders** in `document_processor.py`
2. **Create new tools** in `tools.py`
3. ** dependencies** in `requirements.txt`
4. **Add tests** in the `tests/` directory
5. **Improve documentation** in this README

## 📄 License & Acknowledgments

This project is designed for educational and development purposes, showcasing the use of local AI combined with basic document intelligence.

### **Document Support**

- **📄 Documents**: PDF, TXT, CSV, JSON, DOCX, XLSX, Markdown
- **🎨 Presentations**: PowerPoint (PPTX) with full content extraction
- **🖼️ Images**: JPG, PNG, GIF, BMP with OCR capabilities
- **🌐 Web Content**: Scrape and analyze web pages automatically
- **🎥 YouTube**: Extract and search through video transcripts
- **�️ Databases**: Direct PostgreSQL integration for structured data

### 🏠 **Local**

Everything runs on your machine using Ollama. No data leaves your system, no API keys required, no subscription fees. Your documents, your conversations, your privacy.

## 🚀 Getting Started

### Quick Setup

```bash
# Clone and dive in
git clone <This Repository>
cd <Your Project Directory>
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Start Ollama (if not running)
ollama serve
ollama pull llama3.2:1b

# Launch your AI companion
streamlit run app.py --server.port=8501 # (setting the port is optional)
```

### Environment Setup

Copy `.env.example` to `.env` and configure:

```bash
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b
STREAMLIT_SERVER_PORT=8501
DATABASE_URL=postgresql://user@localhost:5432/dbname  # Optional
```

## 🎯 How to Use

1. **Upload Files** - Drag & drop PDFs, Word docs, slides, images
2. **Process & Analyze** - Click "📁 Process Documents"
3. **Ask Anything** - "What are the key themes across all documents?"
4. **Get Smart Answers** - Cross-document insights with source attribution

### 🌐 Web & YouTube Integration

1. **Web Pages** - Paste public URL and extract content
2. **YouTube Videos** - Add video links to search through transcripts
3. **Mixed Sources** - Combine documents, web, and video content
4. **Unified Search** - Ask questions across all content types

## 🧪 Testing & Debugging

Explore the test suite to check functionality:

```bash
# Document processing demo
streamlit run tests/test_document_processing.py --server.port=8502

# Upload debugging
streamlit run tests/debug_upload.py --server.port=8503

# Similarity search testing
streamlit run tests/test_similarity.py --server.port=8504

# Feedback system demo
streamlit run tests/test_feedback.py --server.port=8505
```

## 📁 Project Architecture

```
windsurf-project/
├── app.py                    # 🎯 Main application
├── document_processor.py     # 📚 Document intelligence core
├── langchain_integration.py  # 🦙 LLM management
├── tools.py                  # 🔧 Utility tools
├── feedback_analytics.py     # 📊 Quality tracking
├── requirements.txt          # 📦 Dependencies
├── .env.example             # 🔧 Configuration template
├── tests/                   # 🧪 Test suite
└── README.md                # 📖 This guide
```

## ⚡  Tips

### 🏎️ Speed Optimisation

- **Use `llama3.2:1b`** for lightning-fast responses
- **Enable Metal GPU** running the shell script will start the application with metal=1 
- **Limit conversations** to 5-10 messages for best performance
- **Process documents in batches** for large files

### 💾 Memory Management

- **Clear processed documents** when switching projects
- **Use smaller chunks** for very large documents
- **Restart periodically** for long sessions

## 🐛 Friendly Troubleshooting

### 🦙 Ollama Issues

```bash
# Check if Ollama is running
ollama list

# Start the server
ollama serve

# Pull recommended model
ollama pull llama3.2:1b
```

### 📄 Document Processing

- **Supported formats**: PDF, TXT, CSV, JSON, DOCX, XLSX, MD, PPTX, JPG, PNG
- **File size limit**: 200MB per file (configurable via the `.streamlit/config.toml` file)
- **Multiple files**: Upload and process simultaneously
- **Cross-document Q&A**: Ask questions spanning all uploaded content

### 🌐 Network Issues

- **Web scraping**: Works with most public websites
- **YouTube transcripts**: Automatic extraction for videos with captions
- **No API keys**: Everything works with free, public APIs



**Special thanks to:**

- **Streamlit** for the web framework
- **Ollama** for making local LLMs accessible
- **LangChain** for powerful document processing
- **DuckDuckGo** for privacy-focused web search
