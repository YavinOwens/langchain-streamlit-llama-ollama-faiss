"""Local Llama Chat with Tools.

A Streamlit application that provides a chat interface using local Llama models
via Ollama, with tool integration for web search, weather, and document Q&A.
"""

import streamlit as st
import ollama
import os
from pathlib import Path
from dotenv import load_dotenv
import time
import json
from datetime import datetime
from langchain_integration import LangChainManager
from tools import TOOL_CATEGORIES, get_tools_by_category, ALL_TOOLS
from document_processor import (
    DocumentProcessor,
    get_supported_extensions,
    is_file_supported,
    is_url_valid,
    is_youtube_url,
)

# Load environment variables
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="Local Llama Chat with Tools",
    page_icon="[LLAMA]",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Custom CSS for better UI
st.markdown(
    """
<style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .stTextInput > div > div > input {
        font-size: 16px;
    }
</style>
""",
    unsafe_allow_html=True,
)


def check_ollama_connection():
    """Check if Ollama is running and accessible"""
    try:
        ollama.list()
        return True
    except Exception as e:
        st.error(f"Cannot connect to Ollama: {e}")
        return False


def get_available_models():
    """Get list of available models"""
    try:
        models = ollama.list()
        if hasattr(models, "models") and models.models:
            return [model.model for model in models.models]
        else:
            return []
    except Exception as e:
        st.error(f"Error fetching models: {e}")
        return []


def pull_model(model_name):
    """Pull a model if not available"""
    try:
        with st.spinner(f"Pulling {model_name} model... This may take a few minutes."):
            ollama.pull(model_name)
        st.success(f"Successfully pulled {model_name}")
        return True
    except Exception as e:
        st.error(f"Error pulling model: {e}")
        return False


def initialize_langchain_manager(
    model_name: str,
    temperature: float,
    conversation_limit: int = 10,
    enable_conversation: bool = True,
) -> LangChainManager:
    """Initialize LangChain manager with selected model and settings."""
    try:
        manager = LangChainManager(
            model_name=model_name,
            temperature=temperature,
            conversation_limit=conversation_limit,
            enable_conversation=enable_conversation,
        )
        return manager
    except Exception as e:
        st.error(f"Failed to initialize LangChain: {e}")
        return None


def get_selected_tools(selected_categories: list) -> list:
    """Get tools based on selected categories."""
    tools = []
    for category in selected_categories:
        tools.extend(get_tools_by_category(category))
    return tools


# Feedback Management Functions


def save_feedback(
    message_id: str,
    feedback: str,
    response_text: str,
    response_time: float,
    tools_used: bool,
):
    """Save feedback to storage."""
    feedback_data = {
        "message_id": message_id,
        "feedback": feedback,
        "response_text": response_text[:200],  # Store first 200 chars
        "response_time": response_time,
        "tools_used": tools_used,
        "timestamp": datetime.now().isoformat(),
    }

    # Initialize feedback storage if not exists
    if "feedback_data" not in st.session_state:
        st.session_state.feedback_data = []

    st.session_state.feedback_data.append(feedback_data)

    # Save to file for persistence
    try:
        with open("feedback_log.json", "a") as f:
            f.write(json.dumps(feedback_data) + "\n")
    except BaseException:
        pass  # Ignore file errors


def get_feedback_analytics() -> dict:
    """Get feedback analytics."""
    if "feedback_data" not in st.session_state:
        # Load from file if available
        try:
            feedback_data = []
            with open("feedback_log.json", "r") as f:
                for line in f:
                    if line.strip():
                        feedback_data.append(json.loads(line))
            st.session_state.feedback_data = feedback_data
        except BaseException:
            st.session_state.feedback_data = []

    feedback_list = st.session_state.feedback_data
    if not feedback_list:
        return {"total": 0, "thumbs_up": 0, "thumbs_down": 0, "avg_response_time": 0}

    thumbs_up = sum(1 for f in feedback_list if f["feedback"] == "up")
    thumbs_down = sum(1 for f in feedback_list if f["feedback"] == "down")
    avg_response_time = sum(f["response_time"] for f in feedback_list) / len(
        feedback_list
    )

    return {
        "total": len(feedback_list),
        "thumbs_up": thumbs_up,
        "thumbs_down": thumbs_down,
        "avg_response_time": round(avg_response_time, 2),
        "satisfaction_rate": round((thumbs_up / len(feedback_list)) * 100, 1)
        if feedback_list
        else 0,
    }


def get_system_improvements() -> list:
    """Get system improvement suggestions based on feedback."""
    analytics = get_feedback_analytics()
    improvements = []

    if analytics["thumbs_down"] > analytics["thumbs_up"]:
        improvements.append(
            "[TOOL] Consider improving response quality - more thumbs down than up"
        )

    if analytics["avg_response_time"] > 5:
        improvements.append("⚡ Response times are slow - consider optimization")

    if analytics["satisfaction_rate"] < 70:
        improvements.append(
            "[STATS] Low satisfaction rate - review tool usage and prompts"
        )

    if analytics["total"] < 10:
        improvements.append("[CHART] Collect more feedback for better insights")

    return improvements


def main():
    """Main application entry point."""
    st.title("[LLAMA] Local Llama Chat with Tools")
    st.markdown("Chat with your local Llama model using Ollama and LangChain")

    # Initialize session state variables FIRST
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "langchain_manager" not in st.session_state:
        st.session_state.langchain_manager = None
    if "feedback_data" not in st.session_state:
        st.session_state.feedback_data = []
    if "document_processor" not in st.session_state:
        st.session_state.document_processor = None

    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")

        # Check Ollama connection
        if st.button("Check Ollama Connection", key="check_connection"):
            if check_ollama_connection():
                st.success("[OK] Ollama is running!")
            else:
                st.error("❌ Cannot connect to Ollama")
                st.info("Make sure Ollama is installed and running: `ollama serve`")

        # Model selection
        st.subheader("Model Selection")
        available_models = get_available_models()

        if available_models:
            selected_model = st.selectbox(
                "Choose a model:", available_models, index=0, key="model_select"
            )
        else:
            st.warning("No models found. Please pull a model first.")
            selected_model = st.text_input(
                "Enter model name to pull:", value="llama3.2:1b", key="model_input"
            )

            if st.button("Pull Model", key="pull_model"):
                if selected_model:
                    pull_model(selected_model)
                    st.rerun()

        # Temperature slider
        temperature = st.slider(
            "Temperature (creativity):",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            key="temperature",
        )

        # Tool selection
        st.subheader("[TOOLS] Tool Selection")
        use_tools = st.checkbox("Enable Tools", value=True, key="use_tools")

        if use_tools:
            selected_categories = st.multiselect(
                "Select tool categories:",
                list(TOOL_CATEGORIES.keys()),
                default=["Mathematics", "Utilities"],
                key="tool_categories",
            )

            # Show selected tools info
            if selected_categories:
                tools = get_selected_tools(selected_categories)
                st.info(
                    f"[TOOL] {len(tools)} tools selected from {len(selected_categories)} categories"
                )

                # Show tool details in expander
                with st.expander("View Selected Tools"):
                    for category in selected_categories:
                        st.write(f"**{category}:**")
                        category_tools = get_tools_by_category(category)
                        for tool in category_tools:
                            st.write(f"  • {tool.name}: {tool.description}")
        else:
            selected_categories = []
            tools = []

        # Conversation settings
        st.subheader("[CHAT] Conversation Settings")
        enable_conversation = st.checkbox(
            "Enable Conversation Memory",
            value=True,
            key="enable_conversation",
            help="Allow the AI to remember and refer to previous messages",
        )

        if enable_conversation:
            conversation_limit = st.slider(
                "Conversation Memory (messages):",
                min_value=5,
                max_value=20,
                value=10,
                step=1,
                key="conversation_limit",
                help="Maximum number of previous messages to remember",
            )

            # Show conversation status
            if (
                "langchain_manager" in st.session_state
                and st.session_state.langchain_manager
            ):
                msg_count = len(st.session_state.langchain_manager.conversation_history)
                st.info(
                    f"[EDIT] Current conversation: {msg_count}/{conversation_limit} messages"
                )

                if st.button("Clear Conversation", key="clear_conversation"):
                    st.session_state.langchain_manager.clear_conversation()
                    st.session_state.messages = []
                    st.rerun()
        else:
            conversation_limit = 10

        # System info
        st.subheader("System Info")
        st.info(f"Host: {os.getenv('OLLAMA_HOST', 'http://localhost:11434')}")

        # Metal GPU status
        st.subheader("[APP] Metal GPU Status")
        try:
            # Check if Metal is being used
            models = ollama.list()
            if hasattr(models, "models") and models.models:
                st.success("[OK] Metal GPU acceleration available")
                st.caption("Apple M2 Metal optimization enabled")
                st.caption("• Memory mapping: ON")
                st.caption("• GPU acceleration: ON")
                st.caption("• Optimized for 8GB RAM")
            else:
                st.info("[REFRESH] Pull a model to enable Metal acceleration")
        except BaseException:
            st.warning("⚠️ Metal status unknown")

        # Clear chat button
        if st.button("Clear Chat History", key="clear_chat"):
            st.session_state.messages = []
            if (
                "langchain_manager" in st.session_state
                and st.session_state.langchain_manager
            ):
                st.session_state.langchain_manager.clear_conversation()
            st.rerun()

        # Feedback Analytics
        st.subheader("[STATS] Feedback Analytics")
        analytics = get_feedback_analytics()

        if analytics["total"] > 0:
            st.metric("Total Responses", analytics["total"])
            col1, col2 = st.columns(2)
            with col1:
                st.metric("[UP] Thumbs Up", analytics["thumbs_up"])
            with col2:
                st.metric("[DOWN] Thumbs Down", analytics["thumbs_down"])

            st.metric("Satisfaction Rate", f"{analytics['satisfaction_rate']}%")
            st.metric("Avg Response Time", f"{analytics['avg_response_time']}s")

            # System improvements
            improvements = get_system_improvements()
            if improvements:
                with st.expander("[TOOL] System Improvement Suggestions"):
                    for improvement in improvements:
                        st.warning(improvement)
        else:
            st.info("No feedback data yet. Rate responses to see analytics!")

        # Enhanced Document Upload Section
        st.subheader("[DOC] Enhanced Document Processing")

        # Initialize document processor
        if st.session_state.document_processor is None and selected_model:
            st.session_state.document_processor = DocumentProcessor(selected_model)
            st.info("[RUN] Enhanced document processor initialized")

        processor = st.session_state.document_processor

        # Tab interface for different input types
        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "[FOLDER] File Upload",
                "[WEB] Web Content",
                "[DB] Database Query",
                "[VIDEO] YouTube Video",
            ]
        )

        with tab1:
            # File upload with enhanced support
            uploaded_files = st.file_uploader(
                "Upload documents for Q&A:",
                accept_multiple_files=True,
                type=get_supported_extensions(),
                help=f"Supported formats: {', '.join(get_supported_extensions())}",
            )

            # Process uploaded files
            if uploaded_files and processor:
                if st.button("[FOLDER] Process Documents", key="process_docs"):
                    with st.spinner("Processing documents..."):
                        success_count = 0
                        for uploaded_file in uploaded_files:
                            if is_file_supported(uploaded_file):
                                if processor.process_uploaded_file(uploaded_file):
                                    success_count += 1
                            else:
                                st.warning(f"Unsupported file: {uploaded_file.name}")

                        if success_count > 0:
                            st.success(
                                f"[OK] Successfully processed {success_count} document(s)"
                            )
                            # Setup QA chain with current LLM if available
                            if (
                                st.session_state.langchain_manager
                                and st.session_state.langchain_manager.llm
                                and processor.vector_store
                            ):
                                if processor.setup_qa_chain(
                                    st.session_state.langchain_manager.llm
                                ):
                                    st.success("[SEARCH] Document Q&A is ready!")
                                else:
                                    st.warning(
                                        "⚠️ Documents processed but QA chain setup failed"
                                    )
                            else:
                                st.warning(
                                    "⚠️ Documents processed but LLM not ready. Initialize model first."
                                )
                        else:
                            st.error("❌ No documents were processed successfully")

        with tab2:
            # Web content processing
            st.write("[WEB] Add web content for Q&A")

            url_input = st.text_input(
                "Enter URL:",
                placeholder="https://example.com or https://example.com/page",
                help="Enter a URL to scrape and add to the knowledge base",
            )

            loader_type = st.selectbox(
                "Loader Type:",
                ["web_base", "recursive"],
                help="Web Base: Single page | Recursive: Multiple pages from the same domain",
            )

            if st.button("[WEB] Process Web Content", key="process_web") and url_input:
                if is_url_valid(url_input):
                    with st.spinner("Processing web content..."):
                        if processor.process_web_url(url_input, loader_type):
                            # Setup QA chain with current LLM if available
                            if (
                                st.session_state.langchain_manager
                                and st.session_state.langchain_manager.llm
                                and processor.vector_store
                            ):
                                if processor.setup_qa_chain(
                                    st.session_state.langchain_manager.llm
                                ):
                                    st.success("[SEARCH] Web content Q&A is ready!")
                                else:
                                    st.warning(
                                        "⚠️ Web content processed but QA chain setup failed"
                                    )
                        else:
                            st.error("❌ Failed to process web content")
                else:
                    st.error("❌ Please enter a valid URL")

        with tab3:
            # Database query processing
            st.write("[DB] Query database for Q&A")

            if processor.db_connection:
                # Show available tables
                tables = processor.get_database_tables()
                if tables:
                    st.write("**Available Tables:**")
                    selected_table = st.selectbox("Select a table to explore:", tables)

                    if selected_table:
                        # Show table schema
                        schema = processor.get_table_schema(selected_table)
                        st.code(schema, language="sql")

                        # Suggested query
                        suggested_query = f"SELECT * FROM {selected_table} LIMIT 50"
                        st.write(f"Suggested query: `{suggested_query}`")
                else:
                    st.info("No tables found in database")

                # Custom SQL query
                sql_query = st.text_area(
                    "Enter SQL Query:",
                    placeholder="SELECT * FROM your_table LIMIT 100",
                    help="Enter a SQL SELECT query to retrieve data for Q&A",
                )

                if (
                    st.button("[DB] Process Database Query", key="process_db")
                    and sql_query
                ):
                    if sql_query.strip().upper().startswith("SELECT"):
                        with st.spinner("Processing database query..."):
                            if processor.process_database_query(sql_query):
                                # Setup QA chain with current LLM if available
                                if (
                                    st.session_state.langchain_manager
                                    and st.session_state.langchain_manager.llm
                                    and processor.vector_store
                                ):
                                    if processor.setup_qa_chain(
                                        st.session_state.langchain_manager.llm
                                    ):
                                        st.success("[SEARCH] Database Q&A is ready!")
                                    else:
                                        st.warning(
                                            "⚠️ Database content processed but QA chain setup failed"
                                        )
                            else:
                                st.error("❌ Failed to process database query")
                    else:
                        st.error("❌ Only SELECT queries are supported for safety")
            else:
                st.warning("⚠️ Database not connected. Check DATABASE_URL in .env file")

        with tab4:
            # YouTube video processing
            st.write("[VIDEO] Add YouTube video transcripts for Q&A")

            youtube_url = st.text_input(
                "Enter YouTube URL:",
                placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                help="Enter a YouTube video URL to extract transcript for Q&A",
            )

            language = st.selectbox(
                "Transcript Language:",
                ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
                help="Select the language for transcript extraction",
            )

            if (
                st.button("[VIDEO] Process YouTube Video", key="process_youtube")
                and youtube_url
            ):
                if is_youtube_url(youtube_url):
                    with st.spinner("Processing YouTube video content..."):
                        success = processor.process_youtube_video(youtube_url, language)

                    if success:
                        st.success("[OK] YouTube video processed successfully!")

                        # Setup QA chain separately
                        with st.spinner("Setting up Q&A chain..."):
                            if (
                                st.session_state.langchain_manager
                                and st.session_state.langchain_manager.llm
                                and processor.vector_store
                            ):
                                if processor.setup_qa_chain(
                                    st.session_state.langchain_manager.llm
                                ):
                                    st.success("[SEARCH] YouTube video Q&A is ready!")
                                else:
                                    st.warning(
                                        "⚠️ YouTube content processed but QA chain setup failed"
                                    )
                            else:
                                st.warning(
                                    "⚠️ YouTube content processed but LLM not ready"
                                )
                    else:
                        st.error("❌ Failed to process YouTube video")
                else:
                    st.error("❌ Please enter a valid YouTube URL")

        # Show processed content
        if processor:
            content_info = processor.get_all_content_info()

            if (
                content_info["total_files"] > 0
                or content_info["total_urls"] > 0
                or content_info["total_tables"] > 0
                or content_info["total_videos"] > 0
            ):
                st.write("**[STATS] Processed Content:**")

                # Files section
                if content_info["total_files"] > 0:
                    st.write(f"[FOLDER] **Files ({content_info['total_files']}):**")
                    for file_info in content_info["files"]:
                        with st.expander(f"[DOC] {file_info['name']}"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Type", file_info["type"].upper())
                            with col2:
                                st.metric("Chunks", file_info["chunks"])
                            with col3:
                                size_kb = file_info["size"] / 1024
                                st.metric("Size", f"{size_kb:.1f} KB")

                # URLs section
                if content_info["total_urls"] > 0:
                    st.write(f"[WEB] **Web Content ({content_info['total_urls']}):**")
                    for url_info in content_info["urls"]:
                        with st.expander(f"[WEB] {url_info['url']}"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Loader", url_info["loader_type"])
                            with col2:
                                st.metric("Documents", url_info["documents"])
                            with col3:
                                st.metric("Chunks", url_info["chunks"])

                # Database section
                if content_info["total_tables"] > 0:
                    st.write(
                        f"[DB] **Database Queries ({content_info['total_tables']}):**"
                    )
                    for table_info in content_info["tables"]:
                        with st.expander(f"[DB] {table_info['query'][:50]}..."):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Type", "SQL Query")
                            with col2:
                                st.metric("Documents", table_info["documents"])
                            with col3:
                                st.metric("Chunks", table_info["chunks"])

                # YouTube section
                if content_info["total_videos"] > 0:
                    st.write(
                        f"[VIDEO] **YouTube Videos ({content_info['total_videos']}):**"
                    )
                    for video_info in content_info["videos"]:
                        video_title = video_info.get("title", "Unknown Video")
                        with st.expander(f"[VIDEO] {video_title}"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Type", "YouTube Video")
                            with col2:
                                st.metric("Documents", video_info["documents"])
                            with col3:
                                st.metric("Chunks", video_info["chunks"])

                            # Additional video info
                            if video_info.get("view_count"):
                                st.write(f"[VIEW] Views: {video_info['view_count']:,}")
                            if video_info.get("length"):
                                st.write(f"⏱️ Length: {video_info['length']} seconds")
                            if video_info.get("description"):
                                st.write(
                                    f"[EDIT] Description: {video_info['description']}"
                                )

                # Summary
                st.metric("[STATS] Total Chunks", content_info["total_chunks"])

                # Clear content button
                if st.button("[DELETE] Clear All Content", key="clear_all_content"):
                    processor.clear_documents()
                    st.rerun()
            else:
                st.info("No content processed yet")

        # Document Q&A status and controls
        if processor and processor.is_ready():
            st.success("[SEARCH] Document Q&A is ready!")

            # Add explicit document Q&A mode
            st.subheader("[DOC] Document Q&A Mode")
            doc_qa_mode = st.checkbox(
                "[DOC] Force Document Q&A (answers only from uploaded content)",
                key="doc_qa_mode",
                help="When enabled, all questions will be answered using only uploaded documents, web content, database queries, and YouTube videos",
            )

            if doc_qa_mode:
                st.info(
                    "[SEARCH] Document Q&A mode is ON - Answers will come from uploaded content only"
                )
        elif processor:
            st.warning(
                "⚠️ Content processed but Q&A not ready. Check LLM initialization."
            )

    # Initialize LangChain manager when model or settings change
    if selected_model and (
        "langchain_manager" not in st.session_state
        or st.session_state.langchain_manager is None
        or st.session_state.langchain_manager.model_name != selected_model
        or st.session_state.langchain_manager.temperature != temperature
        or st.session_state.langchain_manager.conversation_limit != conversation_limit
        or st.session_state.langchain_manager.enable_conversation != enable_conversation
    ):
        with st.spinner("Initializing LangChain..."):
            st.session_state.langchain_manager = initialize_langchain_manager(
                selected_model, temperature, conversation_limit, enable_conversation
            )

            # Set tools if enabled
            if (
                use_tools
                and selected_categories
                and "langchain_manager" in st.session_state
                and st.session_state.langchain_manager
            ):
                tools = get_selected_tools(selected_categories)
                st.session_state.langchain_manager.set_tools(tools)

            # Setup document QA chain if documents are processed
            if (
                st.session_state.document_processor
                and st.session_state.document_processor.vector_store
                and st.session_state.langchain_manager
                and st.session_state.langchain_manager.llm
            ):
                if st.session_state.document_processor.setup_qa_chain(
                    st.session_state.langchain_manager.llm
                ):
                    st.success("[SEARCH] Document Q&A chain updated!")
                else:
                    st.warning("⚠️ Failed to setup document Q&A chain")

    # Display chat messages
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "response_time" in message:
                st.caption(f"Response time: {message['response_time']}s")
            if "tools_used" in message:
                st.caption(f"[TOOL] Tools: {message['tools_used']}")

            # Add feedback buttons for assistant messages
            if message["role"] == "assistant" and "feedback_given" not in message:
                message_id = f"msg_{i}_{hash(message['content']) % 10000}"

                # Use built-in Streamlit feedback widget
                feedback = st.feedback(
                    "thumbs",
                    key=f"feedback_{message_id}",
                    on_change=lambda fid=message_id,
                    txt=message["content"],
                    rt=message.get("response_time", 0),
                    tu="tools_used" in message: save_feedback(
                        fid,
                        "up" if st.session_state[f"feedback_{fid}"] == 1 else "down",
                        txt,
                        rt,
                        tu,
                    ),
                )

                if feedback is not None:
                    # Save feedback
                    feedback_type = "up" if feedback == 1 else "down"
                    save_feedback(
                        message_id,
                        feedback_type,
                        message["content"],
                        message.get("response_time", 0),
                        "tools_used" in message,
                    )
                    message["feedback_given"] = feedback_type
                    st.rerun()
                else:
                    st.caption("[UP] Rate this response")
            elif "feedback_given" in message:
                feedback_emoji = (
                    "[UP]" if message["feedback_given"] == "up" else "[DOWN]"
                )
                st.caption(f"Thanks for your feedback! {feedback_emoji}")

    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        if not available_models and not selected_model:
            st.error("Please select or pull a model first!")
            return

        if (
            "langchain_manager" not in st.session_state
            or not st.session_state.langchain_manager
        ):
            st.error("LangChain manager not initialized!")
            return

        # Check if user wants to ask about documents
        use_document_qa = False
        processor = st.session_state.document_processor

        if processor and processor.is_ready():
            # Check if explicit document Q&A mode is enabled
            if st.session_state.get("doc_qa_mode", False):
                use_document_qa = True
                st.info("[SEARCH] Using document Q&A (forced mode)...")
            else:
                # Check if the question is about documents (automatic detection)
                doc_keywords = [
                    "what",
                    "how",
                    "who",
                    "when",
                    "where",
                    "tell me about",
                    "find",
                    "search",
                ]
                prompt_lower = prompt.lower()
                if any(keyword in prompt_lower for keyword in doc_keywords):
                    use_document_qa = True
                    st.info("[SEARCH] Using document Q&A...")

        # Add user message to chat history and conversation
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.langchain_manager.add_message("user", prompt)
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        response_text = ""
        response_time = 0

        if use_document_qa:
            # Use document Q&A
            doc_result = processor.answer_question(prompt)
            if doc_result["success"]:
                # Show the retrieved context for debugging
                context_preview = ""
                if doc_result.get("source_documents"):
                    context_preview = "\n\n**Retrieved Context:**\n"
                    for i, doc in enumerate(
                        doc_result["source_documents"][:2]
                    ):  # Show first 2 docs
                        source = doc.metadata.get("source", "Unknown")
                        content_preview = doc.page_content[:150]
                        context_preview += (
                            f"Doc {i + 1} ({source}): {content_preview}...\n"
                        )

                response_text = f"[DOC] **Document Answer:**\n\n{doc_result['answer']}{context_preview}"
                response_time = 2.0
            else:
                # Fall back to regular response
                response_text, response_time = (
                    st.session_state.langchain_manager.generate_response(
                        prompt, use_tools=use_tools
                    )
                )
        else:
            # Use regular chat with tools
            response_text, response_time = (
                st.session_state.langchain_manager.generate_response(
                    prompt, use_tools=use_tools
                )
            )

        if response_text:
            # Add assistant message to conversation history
            st.session_state.langchain_manager.add_message("assistant", response_text)

            # Create message metadata
            message_data = {
                "role": "assistant",
                "content": response_text,
                "response_time": response_time,
            }

            # Add tools info if tools were used
            if use_tools and selected_categories:
                message_data["tools_used"] = (
                    f"{len(get_selected_tools(selected_categories))} tools"
                )

            # Add assistant message to chat history
            st.session_state.messages.append(message_data)

            with st.chat_message("assistant"):
                st.markdown(response_text)
                st.caption(f"Response time: {response_time}s")
                if use_tools and selected_categories:
                    st.caption(
                        f"[TOOL] Tools: {len(get_selected_tools(selected_categories))} tools"
                    )

    # Footer
    st.markdown("---")
    st.markdown("[TIP] **User Tip:**")
    st.markdown(
        "- Use smaller models (like `llama3.2:1b`) for better performance on 8GB RAM, This tool was built for example purposes"
    )


if __name__ == "__main__":
    main()
