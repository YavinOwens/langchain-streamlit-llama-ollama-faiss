"""
Document Processing Module for LangChain
Handles file uploads, web scraping, database queries, document parsing, and vector storage for Q&A
"""

import os
import tempfile
from typing import List, Dict, Any, Optional
import streamlit as st
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    CSVLoader,
    JSONLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
    WebBaseLoader,
    RecursiveUrlLoader,
    UnstructuredMarkdownLoader,
    UnstructuredPowerPointLoader,
    UnstructuredImageLoader,
)
import os
from pathlib import Path

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    import yt_dlp

    YOUTUBE_AVAILABLE = True
except ImportError:
    YouTubeTranscriptApi = None
    yt_dlp = None
    YOUTUBE_AVAILABLE = False
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from sqlalchemy import create_engine, inspect, text
import pandas as pd

# Try the new import location first, fallback to old
try:
    from langchain.chains.combine_documents.stuff import StuffDocumentsChain
    from langchain.chains.llm import LLMChain
    from langchain.chains.question_answering import load_qa_chain

    HAS_NEW_CHAINS = True
except ImportError:
    try:
        from langchain.chains import RetrievalQA

        HAS_NEW_CHAINS = False
    except ImportError:
        # Create a simple fallback QA implementation
        HAS_NEW_CHAINS = False


class DocumentProcessor:
    """Handles document processing with web scraping, database queries, and enhanced file types"""

    def __init__(self, model_name: str = "llama3.2:1b"):
        self.model_name = model_name
        self.embeddings = None
        self.vector_store = None
        self.qa_chain = None
        self.processed_files = []
        self.processed_urls = []
        self.processed_tables = []
        self.processed_videos = []
        self.db_connection = None
        self.sql_db = None
        self._initialize_embeddings()
        self._initialize_database()

    def _initialize_embeddings(self):
        """Initialize Ollama embeddings"""
        try:
            self.embeddings = OllamaEmbeddings(model=self.model_name)
        except Exception as e:
            st.error(f"Failed to initialize embeddings: {e}")
            self.embeddings = None

    def _initialize_database(self):
        """Initialize database connection from environment variables"""
        try:
            database_url = os.getenv("DATABASE_URL")
            if database_url:
                self.db_connection = create_engine(database_url)
                self.sql_db = SQLDatabase.from_uri(database_url)
                st.success("[OK] Database connection established")
            else:
                st.info("[DOC] No DATABASE_URL found - database features disabled")
        except Exception as e:
            st.error(f"Failed to initialize database: {e}")
            self.db_connection = None
            self.sql_db = None

    def load_document(self, file_path: str, file_type: str) -> List[Document]:
        """Load document based on file type"""
        try:
            if file_type == "pdf":
                loader = PyPDFLoader(file_path)
            elif file_type == "txt":
                loader = TextLoader(file_path, encoding="utf-8")
            elif file_type == "csv":
                loader = CSVLoader(file_path)
            elif file_type == "json":
                # For JSON, try a simpler approach
                loader = TextLoader(file_path, encoding="utf-8")
            elif file_type == "docx":
                loader = Docx2txtLoader(file_path)
            elif file_type in ["xlsx", "xls"]:
                loader = UnstructuredExcelLoader(file_path)
            elif file_type == "md":
                loader = UnstructuredMarkdownLoader(file_path)
            elif file_type == "pptx":
                loader = UnstructuredPowerPointLoader(file_path)
            elif file_type in ["jpg", "jpeg", "png", "gif", "bmp"]:
                loader = UnstructuredImageLoader(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

            documents = loader.load()
            st.success(f"[OK] Loaded {len(documents)} document(s) from {file_type}")
            return documents
        except Exception as e:
            st.error(f"Error loading {file_type} file: {e}")
            return []

    def load_web_content(
        self, url: str, loader_type: str = "web_base"
    ) -> List[Document]:
        """Load content from web URL"""
        try:
            if loader_type == "web_base":
                loader = WebBaseLoader(url)
            elif loader_type == "recursive":
                loader = RecursiveUrlLoader(url, max_depth=2, prevent_outside=True)
            else:
                loader = WebBaseLoader(url)

            documents = loader.load()
            st.success(f"[OK] Loaded {len(documents)} document(s) from {url}")
            return documents
        except Exception as e:
            st.error(f"Error loading web content from {url}: {e}")
            return []

    def load_youtube_content(
        self, video_url: str, language: str = "en"
    ) -> List[Document]:
        """Load transcript from YouTube video using youtube-transcript-api directly"""
        if not YOUTUBE_AVAILABLE:
            st.error(
                "YouTube libraries not available. Please install youtube-transcript-api and yt-dlp"
            )
            return []

        try:
            # Extract video ID from URL
            import re

            video_id_match = re.search(
                r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
                video_url,
            )
            if not video_id_match:
                st.error("Invalid YouTube URL format")
                return []

            video_id = video_id_match.group(1)

            # Get video metadata using yt-dlp
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "extract_flat": True,
            }

            video_info = {}
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=False)
                    video_info = {
                        "title": info.get("title", "Unknown Video"),
                        "description": info.get("description", ""),
                        "uploader": info.get("uploader", ""),
                        "duration": info.get("duration", 0),
                        "view_count": info.get("view_count", 0),
                        "upload_date": info.get("upload_date", ""),
                    }
            except Exception as e:
                st.warning(f"Could not fetch video metadata: {e}")
                video_info = {
                    "title": "Unknown Video",
                    "description": "",
                    "uploader": "",
                    "duration": 0,
                    "view_count": 0,
                    "upload_date": "",
                }

            # Get transcript using youtube-transcript-api
            try:
                # Create API instance
                api = YouTubeTranscriptApi()

                # Try to get transcript directly
                transcript = None
                transcript_source = "none"

                # Try manual transcript first
                try:
                    transcript = api.fetch(video_id, languages=["en"])
                    transcript_source = "manual"
                except Exception as e:
                    # Try auto-generated transcript
                    try:
                        # Get transcript list and find generated one
                        transcript_list = api.list(video_id)
                        generated_transcript = (
                            transcript_list.find_generated_transcript(["en"])
                        )
                        transcript = generated_transcript.fetch()
                        transcript_source = "auto_generated"
                    except Exception as e2:
                        # Try any available transcript
                        try:
                            transcript = api.fetch(video_id)
                            transcript_source = "fallback"
                        except Exception as e3:
                            print(f"Could not fetch any transcript: {e}, {e2}, {e3}")

                if not transcript:
                    st.warning(f"No transcript available for this video")
                    return []

                # Combine transcript text
                transcript_text = " ".join([entry.text for entry in transcript])

                # Create content
                content = f"YouTube Video Transcript: {video_info['title']}\n"
                content += f"Uploader: {video_info['uploader']}\n"
                content += f"Duration: {video_info['duration']} seconds ({
                    video_info['duration'] // 60
                }:{video_info['duration'] % 60:02d})\n"
                content += f"Views: {video_info['view_count']:,}\n"
                content += f"Transcript Source: {transcript_source}\n\n"
                content += f"Transcript:\n{transcript_text}"

                # Create document with metadata
                metadata = {
                    "source": video_url,
                    "title": video_info["title"],
                    "description": video_info["description"][:500]
                    if video_info["description"]
                    else "",
                    "view_count": video_info["view_count"],
                    "length": video_info["duration"],
                    "upload_date": video_info["upload_date"],
                    "uploader": video_info["uploader"],
                    "language": language,
                    "content_type": "youtube_transcript",
                    "transcript_source": transcript_source,
                    "video_id": video_id,
                }

                document = Document(page_content=content, metadata=metadata)

                st.success(
                    f"[OK] Loaded {transcript_source} transcript from YouTube video: {video_info['title']}"
                )
                st.info(f"[EDIT] Transcript length: {len(transcript_text)} characters")

                return [document]

            except Exception as e:
                st.error(f"Could not fetch transcript: {e}")
                return []

        except Exception as e:
            st.error(f"Error loading YouTube content from {video_url}: {e}")
            return []

    def get_database_tables(self) -> List[str]:
        """Get list of tables in the database"""
        if not self.db_connection:
            return []

        try:
            inspector = inspect(self.db_connection)
            tables = inspector.get_table_names()
            return tables
        except Exception as e:
            st.error(f"Error getting database tables: {e}")
            return []

    def get_table_schema(self, table_name: str) -> str:
        """Get schema information for a specific table"""
        if not self.db_connection:
            return ""

        try:
            # Suppress SQLAlchemy warnings about vector types
            import warnings
            from sqlalchemy.exc import SAWarning

            warnings.filterwarnings("ignore", category=SAWarning)

            inspector = inspect(self.db_connection)
            columns = inspector.get_columns(table_name)

            schema = f"Table: {table_name}\n"
            schema += "Columns:\n"
            for col in columns:
                # Handle vector column types gracefully
                col_type = str(col["type"])
                if "vector" in col_type.lower():
                    col_type = "VECTOR"
                schema += f"  - {col['name']}: {col_type}\n"

            return schema
        except Exception as e:
            st.error(f"Error getting table schema: {e}")
            return ""

    def query_database_to_documents(
        self, query: str, limit: int = 100
    ) -> List[Document]:
        """Execute SQL query and convert results to documents"""
        if not self.db_connection:
            st.error("Database not connected")
            return []

        try:
            # Execute the query
            df = pd.read_sql(query, self.db_connection)

            if df.empty:
                st.warning("Query returned no results")
                return []

            # Convert DataFrame to documents
            documents = []

            # Create a summary document
            summary_doc = Document(
                page_content=f"SQL Query Results Summary:\nQuery: {query}\nTotal Rows: {
                    len(df)
                }\nColumns: {', '.join(df.columns)}\n\nFirst few rows:\n{
                    df.head().to_string()
                }",
                metadata={
                    "source": "database_query",
                    "query": query,
                    "type": "summary",
                },
            )
            documents.append(summary_doc)

            # Create documents for each row (for small datasets)
            if len(df) <= 20:
                for idx, row in df.iterrows():
                    content = f"Row {idx + 1}:\n"
                    for col in df.columns:
                        content += f"{col}: {row[col]}\n"

                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": "database_query",
                            "query": query,
                            "row": idx,
                            "type": "row",
                        },
                    )
                    documents.append(doc)
            else:
                # For larger datasets, create chunked documents
                chunk_size = 10
                for i in range(0, len(df), chunk_size):
                    chunk = df.iloc[i:i + chunk_size]
                    content = f"Rows {i + 1}-{min(i + chunk_size, len(df))}:\n{chunk.to_string()}"

                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": "database_query",
                            "query": query,
                            "chunk": i // chunk_size,
                            "type": "chunk",
                        },
                    )
                    documents.append(doc)

            st.success(
                f"[OK] Created {len(documents)} documents from {len(df)} database rows"
            )
            return documents

        except Exception as e:
            st.error(f"Error executing database query: {e}")
            return []

    def process_database_query(self, query: str) -> bool:
        """Process database query and add to vector store"""
        if not query or not self.embeddings or not self.db_connection:
            st.error(
                f"Cannot process query: query={bool(query)}, embeddings={
                    bool(self.embeddings)
                }, db={bool(self.db_connection)}"
            )
            return False

        try:
            st.info(f"[DB] Processing database query...")

            # Query database and convert to documents
            documents = self.query_database_to_documents(query)
            if not documents:
                st.error("❌ No documents created from database query")
                return False

            st.info(f"[LIST] Created {len(documents)} document(s) from database")

            # Split into chunks
            chunks = self.split_documents(documents)
            if not chunks:
                st.error("❌ No chunks created")
                return False

            st.info(f"[NUM] Created {len(chunks)} chunks")

            # Add to existing vector store or create new one
            if self.vector_store is None:
                st.info("[BUILD] Creating new vector store...")
                success = self.create_vector_store(chunks)
            else:
                st.info("➕ Adding to existing vector store...")
                # Add to existing vector store
                try:
                    self.vector_store.add_documents(chunks)
                    success = True
                    st.success("[OK] Added database content to vector store")
                except Exception as e:
                    st.error(f"❌ Failed to add database content to vector store: {e}")
                    success = False

            if success:
                self.processed_tables.append(
                    {"query": query, "chunks": len(chunks), "documents": len(documents)}
                )
                st.success(f"[OK] Successfully processed database query")
            else:
                st.error(f"❌ Failed to process database query")

            return success

        except Exception as e:
            st.error(f"Error processing database query: {e}")
            import traceback

            st.error(traceback.format_exc())
            return False

    def split_documents(
        self,
        documents: List[Document],
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> List[Document]:
        """Split documents into chunks for processing"""
        if not documents:
            return []

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
        )

        chunks = text_splitter.split_documents(documents)
        return chunks

    def create_vector_store(self, chunks: List[Document]) -> bool:
        """Create FAISS vector store from document chunks"""
        if not chunks or not self.embeddings:
            return False

        try:
            # Create vector store
            self.vector_store = FAISS.from_documents(chunks, self.embeddings)
            return True
        except Exception as e:
            st.error(f"Error creating vector store: {e}")
            return False

    def setup_qa_chain(self, llm) -> bool:
        """Setup Q&A chain with the vector store"""
        if not self.vector_store or not llm:
            return False

        try:
            # Try new LangChain approach first
            if HAS_NEW_CHAINS:
                # Create custom QA chain using new LangChain pattern
                from langchain_core.runnables import (
                    RunnablePassthrough,
                    RunnableParallel,
                )

                prompt = self._get_qa_prompt()

                def format_docs(docs):
                    """Format documents for display."""
                    return "\n\n".join(doc.page_content for doc in docs)

                # Use a more comprehensive retriever
                retriever = self.vector_store.as_retriever(
                    search_type="similarity_score_threshold",
                    search_kwargs={
                        "k": 10,  # Increased from 3 to 10
                        "score_threshold": 0.3,  # Lower threshold for more results
                    },
                )

                # Create the chain
                self.qa_chain = RunnableParallel(
                    {
                        "context": retriever | format_docs,
                        "question": RunnablePassthrough(),
                    }
                ) | {
                    "answer": prompt | llm,
                    "documents": retriever,
                }
            else:
                # Fallback to simple implementation
                self.qa_chain = self._create_simple_qa_chain(llm)

            return True
        except Exception as e:
            st.error(f"Error setting up QA chain: {e}")
            # Fallback to simple implementation
            try:
                self.qa_chain = self._create_simple_qa_chain(llm)
                return True
            except BaseException:
                return False

    def _create_simple_qa_chain(self, llm):
        """Create a simple QA chain as fallback"""

        def simple_qa(question):
            """Simple QA function as fallback."""
            try:
                # Retrieve relevant documents - get more for better coverage
                docs = self.vector_store.similarity_search(
                    question, k=10
                )  # Increased from 5 to 10
                if not docs:
                    return {
                        "answer": "No relevant information found in documents.",
                        "success": False,
                    }

                # If we have multiple sources, ensure we get diverse content
                if len(docs) > 5:
                    # Try to get documents from different sources
                    unique_sources = set()
                    diverse_docs = []

                    # First, add one doc from each unique source
                    for doc in docs:
                        source = doc.metadata.get("source", "Unknown")
                        if source not in unique_sources:
                            unique_sources.add(source)
                            diverse_docs.append(doc)
                            if len(diverse_docs) >= 5:  # Get up to 5 different sources
                                break

                    # Add remaining docs if we have space
                    for doc in docs:
                        if doc not in diverse_docs and len(diverse_docs) < 8:
                            diverse_docs.append(doc)

                    docs = diverse_docs

                # Format context with better structure
                context_parts = []
                for i, doc in enumerate(docs):
                    source = doc.metadata.get("source", "Unknown")
                    # Truncate very long content to avoid context overflow
                    content = doc.page_content
                    if len(content) > 1000:
                        content = content[:1000] + "..."
                    context_parts.append(
                        f"Document {i + 1} (Source: {source}): {content}"
                    )

                context = "\n\n".join(context_parts)

                # Create more explicit prompt
                prompt_text = f"""You are a helpful assistant that answers questions based ONLY on the provided document context.

CONTEXT:
{context}

QUESTION: {question}

INSTRUCTIONS:
1. Answer based ONLY on the context provided above
2. If the context contains the answer, provide it clearly
3. If the context does not contain the answer, say "I cannot find the answer in the provided documents"
4. Be specific and include numbers/facts from the context when available
5. If the answer comes from a web source, mention that it's from web content
6. Look through ALL provided documents before concluding the answer isn't available

Answer:"""

                # Get response from LLM
                from langchain_core.messages import HumanMessage

                messages = [HumanMessage(content=prompt_text)]
                response = llm.invoke(messages)

                return {
                    "result": response.content,
                    "source_documents": docs,
                    "success": True,
                }
            except Exception as e:
                return {
                    "result": f"Error processing question: {e}",
                    "source_documents": [],
                    "success": False,
                }

        return simple_qa

    def _get_qa_prompt(self) -> PromptTemplate:
        """Get Q&A prompt template"""
        template = """Use the following pieces of context to answer the question at the end.
        If you don't know the answer from the context, just say that you don't know, don't try to make up an answer.
        Use three sentences maximum and keep the answer as concise as possible.

        Context: {context}

        Question: {question}

        Helpful Answer:"""

        return PromptTemplate(
            template=template, input_variables=["context", "question"]
        )

    def answer_question(self, question: str) -> Dict[str, Any]:
        """Answer a question using the processed documents"""
        if not self.qa_chain:
            return {
                "answer": "No documents have been processed yet. Please upload documents or add web content first.",
                "source_documents": [],
                "success": False,
            }

        try:
            # Handle different chain types
            if callable(self.qa_chain):
                # Simple chain function
                result = self.qa_chain(question)
                if isinstance(result, dict):
                    # Add debug info
                    if result.get("source_documents"):
                        sources = set(
                            doc.metadata.get("source", "Unknown")
                            for doc in result["source_documents"]
                        )
                        st.info(
                            f"[SEARCH] Retrieved {len(result['source_documents'])} documents from {len(sources)} sources"
                        )

                    return {
                        "answer": result.get("result", "No answer found."),
                        "source_documents": result.get("source_documents", []),
                        "success": result.get("success", True),
                    }
                else:
                    return {
                        "answer": str(result),
                        "source_documents": [],
                        "success": True,
                    }
            else:
                # LangChain Runnable
                result = self.qa_chain.invoke(question)
                if isinstance(result, dict):
                    # Add debug info
                    if result.get("documents"):
                        sources = set(
                            doc.metadata.get("source", "Unknown")
                            for doc in result["documents"]
                        )
                        st.info(
                            f"[SEARCH] Retrieved {len(result['documents'])} documents from {len(sources)} sources"
                        )

                    return {
                        "answer": result.get("answer", "No answer found."),
                        "source_documents": result.get("documents", []),
                        "success": True,
                    }
                else:
                    return {
                        "answer": str(result),
                        "source_documents": [],
                        "success": True,
                    }
        except Exception as e:
            return {
                "answer": f"Error processing question: {e}",
                "source_documents": [],
                "success": False,
            }

    def process_uploaded_file(self, uploaded_file) -> bool:
        """Process an uploaded file and add to vector store"""
        if not uploaded_file or not self.embeddings:
            st.error(
                f"Cannot process file: uploaded_file={bool(uploaded_file)}, embeddings={bool(self.embeddings)}"
            )
            return False

        try:
            st.info(f"[REFRESH] Processing {uploaded_file.name}...")

            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}"
            ) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name

            # Get file type
            file_type = uploaded_file.name.split(".")[-1].lower()
            st.info(f"[DOC] File type: {file_type}")

            # Load and process document
            documents = self.load_document(tmp_file_path, file_type)
            if not documents:
                st.error("❌ No documents loaded")
                Path(tmp_file_path).unlink()
                return False

            st.info(f"[LIST] Loaded {len(documents)} document(s)")

            # Split into chunks
            chunks = self.split_documents(documents)
            if not chunks:
                st.error("❌ No chunks created")
                Path(tmp_file_path).unlink()
                return False

            st.info(f"[NUM] Created {len(chunks)} chunks")

            # Add to existing vector store or create new one
            if self.vector_store is None:
                st.info("[BUILD] Creating new vector store...")
                success = self.create_vector_store(chunks)
            else:
                st.info("➕ Adding to existing vector store...")
                # Add to existing vector store
                try:
                    self.vector_store.add_documents(chunks)
                    success = True
                    st.success("[OK] Added to vector store")
                except Exception as e:
                    st.error(f"❌ Failed to add to vector store: {e}")
                    success = False

            # Clean up temporary file
            Path(tmp_file_path).unlink()

            if success:
                self.processed_files.append(
                    {
                        "name": uploaded_file.name,
                        "type": file_type,
                        "chunks": len(chunks),
                        "size": len(uploaded_file.getvalue()),
                    }
                )
                st.success(f"[OK] Successfully processed {uploaded_file.name}")
            else:
                st.error(f"❌ Failed to process {uploaded_file.name}")

            return success

        except Exception as e:
            st.error(f"Error processing file: {e}")
            import traceback

            st.error(traceback.format_exc())
            return False

    def process_web_url(self, url: str, loader_type: str = "web_base") -> bool:
        """Process web content and add to vector store"""
        if not url or not self.embeddings:
            st.error(
                f"Cannot process URL: url={bool(url)}, embeddings={bool(self.embeddings)}"
            )
            return False

        try:
            st.info(f"[WEB] Processing web content from {url}...")

            # Load and process web content
            documents = self.load_web_content(url, loader_type)
            if not documents:
                st.error("❌ No web content loaded")
                return False

            st.info(f"[LIST] Loaded {len(documents)} document(s) from web")

            # Split into chunks
            chunks = self.split_documents(documents)
            if not chunks:
                st.error("❌ No chunks created")
                return False

            st.info(f"[NUM] Created {len(chunks)} chunks")

            # Add to existing vector store or create new one
            if self.vector_store is None:
                st.info("[BUILD] Creating new vector store...")
                success = self.create_vector_store(chunks)
            else:
                st.info("➕ Adding to existing vector store...")
                # Add to existing vector store
                try:
                    self.vector_store.add_documents(chunks)
                    success = True
                    st.success("[OK] Added web content to vector store")
                except Exception as e:
                    st.error(f"❌ Failed to add web content to vector store: {e}")
                    success = False

            if success:
                self.processed_urls.append(
                    {
                        "url": url,
                        "loader_type": loader_type,
                        "chunks": len(chunks),
                        "documents": len(documents),
                    }
                )
                st.success(f"[OK] Successfully processed web content from {url}")
            else:
                st.error(f"❌ Failed to process web content from {url}")

            return success

        except Exception as e:
            st.error(f"Error processing web content: {e}")
            import traceback

            st.error(traceback.format_exc())
            return False

    def process_youtube_video(self, video_url: str, language: str = "en") -> bool:
        """Process YouTube video transcript and add to vector store"""
        if not video_url or not self.embeddings:
            st.error(
                f"Cannot process video: video_url={bool(video_url)}, embeddings={bool(self.embeddings)}"
            )
            return False

        try:
            # Load and process YouTube transcript
            documents = self.load_youtube_content(video_url, language)
            if not documents:
                st.error("❌ No YouTube content loaded")
                return False

            # Split into chunks
            chunks = self.split_documents(documents)
            if not chunks:
                st.error("❌ No chunks created")
                return False

            # Add to existing vector store or create new one
            if self.vector_store is None:
                success = self.create_vector_store(chunks)
            else:
                # Add to existing vector store
                try:
                    self.vector_store.add_documents(chunks)
                    success = True
                except Exception as e:
                    st.error(f"❌ Failed to add YouTube content to vector store: {e}")
                    success = False

            if success:
                # Extract video info from metadata
                video_info = {
                    "url": video_url,
                    "language": language,
                    "chunks": len(chunks),
                    "documents": len(documents),
                }
                if documents and documents[0].metadata:
                    metadata = documents[0].metadata
                    video_info.update(
                        {
                            "title": metadata.get("title", "Unknown"),
                            "description": metadata.get("description", "")[:100] + "..."
                            if metadata.get("description")
                            else "",
                            "view_count": metadata.get("view_count", 0),
                            "length": metadata.get("length", 0),
                        }
                    )

                self.processed_videos.append(video_info)

            return success

        except Exception as e:
            st.error(f"Error processing YouTube video: {e}")
            import traceback

            st.error(traceback.format_exc())
            return False

    def get_document_info(self) -> List[Dict[str, Any]]:
        """Get information about processed documents"""
        return self.processed_files

    def get_web_info(self) -> List[Dict[str, Any]]:
        """Get information about processed web content"""
        return self.processed_urls

    def get_database_info(self) -> List[Dict[str, Any]]:
        """Get information about processed database queries"""
        return self.processed_tables

    def get_youtube_info(self) -> List[Dict[str, Any]]:
        """Get information about processed YouTube videos"""
        return self.processed_videos

    def get_all_content_info(self) -> Dict[str, Any]:
        """Get information about all processed content"""
        return {
            "files": self.processed_files,
            "urls": self.processed_urls,
            "tables": self.processed_tables,
            "videos": self.processed_videos,
            "total_files": len(self.processed_files),
            "total_urls": len(self.processed_urls),
            "total_tables": len(self.processed_tables),
            "total_videos": len(self.processed_videos),
            "total_chunks": sum(f["chunks"] for f in self.processed_files)
            + sum(u["chunks"] for u in self.processed_urls)
            + sum(t["chunks"] for t in self.processed_tables)
            + sum(v["chunks"] for v in self.processed_videos),
        }

    def clear_documents(self):
        """Clear all processed documents, web content, database queries, and YouTube videos"""
        self.vector_store = None
        self.qa_chain = None
        self.processed_files = []
        self.processed_urls = []
        self.processed_tables = []
        self.processed_videos = []

    def is_ready(self) -> bool:
        """Check if the processor is ready for Q&A"""
        return self.vector_store is not None and self.qa_chain is not None


# Supported file types
SUPPORTED_FILE_TYPES = {
    "pdf": ["application/pdf"],
    "txt": ["text/plain"],
    "csv": ["text/csv"],
    "json": ["application/json"],
    "docx": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
    "xlsx": ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
    "xls": ["application/vnd.ms-excel"],
    "md": ["text/markdown"],
    "pptx": [
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    ],
    "jpg": ["image/jpeg"],
    "jpeg": ["image/jpeg"],
    "png": ["image/png"],
    "gif": ["image/gif"],
    "bmp": ["image/bmp"],
}


def get_supported_extensions() -> List[str]:
    """Get list of supported file extensions"""
    return list(SUPPORTED_FILE_TYPES.keys())


def is_file_supported(file) -> bool:
    """Check if file type is supported"""
    file_extension = file.name.split(".")[-1].lower()
    return file_extension in SUPPORTED_FILE_TYPES


def is_url_valid(url: str) -> bool:
    """Check if URL is valid"""
    return url.startswith(("http://", "https://"))


def is_youtube_url(url: str) -> bool:
    """Check if URL is a YouTube URL"""
    youtube_domains = ["youtube.com", "youtu.be", "m.youtube.com"]
    return any(domain in url for domain in youtube_domains)
