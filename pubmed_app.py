"""
🔬 Enhanced PubMed Research Hub
Advanced biomedical literature search with improved metadata parsing, enhanced text visibility, and AI-powered Q&A capabilities
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import re
import textwrap

# Try to import PubMed utilities and Ollama for Q&A
try:
    from langchain_community.utilities.pubmed import PubMedAPIWrapper
    PUBMED_AVAILABLE = True
except ImportError:
    PUBMED_AVAILABLE = False

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Configure page
st.set_page_config(
    page_title="PubMed Research Hub",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling and text visibility
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .search-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f7fafc;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4299e1;
    }
    .result-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }
    .scrollable-text {
        max-height: 300px;
        overflow-y: auto;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    .abstract-text {
        max-height: 200px;
        overflow-y: auto;
        padding: 1rem;
        background: #f1f3f4;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        font-size: 0.9rem;
        line-height: 1.5;
    }
    .qa-container {
        background: #f0f8ff;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #b3d9ff;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class EnhancedPubMedHub:
    """Enhanced PubMed research platform with improved parsing, text visibility, and Q&A capabilities"""
    
    def __init__(self):
        self.api_wrapper = None
        self.setup_pubmed()
        
    def setup_pubmed(self):
        """Initialize PubMed API connection"""
        if PUBMED_AVAILABLE:
            try:
                self.api_wrapper = PubMedAPIWrapper(
                    top_k_results=20,
                    email="researcher@example.com"
                )
                return True
            except Exception as e:
                # Only show error if running in Streamlit
                try:
                    st.error(f"❌ Failed to initialize PubMed: {e}")
                except:
                    print(f"Failed to initialize PubMed: {e}")
                return False
        return False
    
    def search_literature(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """Execute PubMed search and return structured results"""
        if not self.api_wrapper:
            return []
        
        try:
            # Update result limit
            self.api_wrapper.top_k_results = max_results
            
            # Perform search
            with st.spinner(f"🔍 Searching PubMed for: '{query}'..."):
                raw_results = self.api_wrapper.run(query)
            
            # Parse results
            parsed_results = self.parse_pubmed_results(raw_results)
            
            return parsed_results
            
        except Exception as e:
            st.error(f"❌ Search failed: {e}")
            return []
    
    def parse_pubmed_results(self, raw_results: str) -> List[Dict[str, Any]]:
        """Enhanced parsing of PubMed results with better metadata extraction"""
        articles = []
        
        # Split by article separators
        article_blocks = raw_results.split('\n\n')
        
        for i, block in enumerate(article_blocks):
            if block.strip():
                article = self.parse_single_article_enhanced(block, i + 1)
                if article:
                    articles.append(article)
        
        return articles
    
    def parse_single_article_enhanced(self, text: str, index: int) -> Optional[Dict[str, Any]]:
        """Enhanced article parsing with better metadata extraction"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        article = {
            'index': index,
            'title': '',
            'authors': '',
            'journal': '',
            'pub_date': '',
            'pmid': '',
            'abstract': '',
            'doi': '',
            'keywords': '',
            'mesh_terms': '',
            'publication_type': '',
            'copyright': '',
            'full_text': '',
            'raw_text': text
        }
        
        current_field = None
        
        for line in lines:
            line_lower = line.lower()
            
            # Enhanced field detection
            if line_lower.startswith('title:') or line_lower.startswith('article:'):
                current_field = 'title'
                article['title'] = line.split(':', 1)[1].strip()
            elif line_lower.startswith('author') or line_lower.startswith('authors:'):
                current_field = 'authors'
                article['authors'] = line.split(':', 1)[1].strip()
            elif line_lower.startswith('journal') or line_lower.startswith('source:') or line_lower.startswith('journal:'):
                current_field = 'journal'
                article['journal'] = line.split(':', 1)[1].strip()
            elif line_lower.startswith('pmid') or line_lower.startswith('pubmed id:'):
                current_field = 'pmid'
                article['pmid'] = line.split(':', 1)[1].strip()
            elif line_lower.startswith('abstract') or line_lower.startswith('summary:'):
                current_field = 'abstract'
                article['abstract'] = line.split(':', 1)[1].strip()
            elif line_lower.startswith('doi'):
                current_field = 'doi'
                article['doi'] = line.split(':', 1)[1].strip()
            elif line_lower.startswith('date') or line_lower.startswith('published'):
                current_field = 'pub_date'
                article['pub_date'] = line.split(':', 1)[1].strip()
            elif line_lower.startswith('keyword'):
                current_field = 'keywords'
                article['keywords'] = line.split(':', 1)[1].strip()
            elif line_lower.startswith('mesh'):
                current_field = 'mesh_terms'
                article['mesh_terms'] = line.split(':', 1)[1].strip()
            elif line_lower.startswith('type') or line_lower.startswith('publication type'):
                current_field = 'publication_type'
                article['publication_type'] = line.split(':', 1)[1].strip()
            elif line_lower.startswith('copyright'):
                current_field = 'copyright'
                article['copyright'] = line.split(':', 1)[1].strip()
            else:
                # Continue with current field or add to full text
                if current_field and current_field in article:
                    article[current_field] += ' ' + line
                else:
                    # Add to full text for Q&A
                    article['full_text'] += ' ' + line
        
        # Clean up full text
        article['full_text'] = article['full_text'].strip()
        
        # Extract title if not found
        if not article['title'] and lines:
            potential_title = lines[0]
            if ':' not in potential_title[:20]:  # Likely not a field
                article['title'] = potential_title
        
        return article if article['title'] or article['abstract'] else None
    
    def create_dataframe(self, articles: List[Dict[str, Any]]) -> pd.DataFrame:
        """Convert articles to pandas DataFrame"""
        if not articles:
            return pd.DataFrame()
        
        df = pd.DataFrame(articles)
        
        # Reorder columns for better display
        column_order = [
            'index', 'title', 'authors', 'journal', 'pub_date', 
            'pmid', 'doi', 'abstract', 'keywords', 'mesh_terms', 
            'publication_type'
        ]
        
        # Keep only existing columns
        existing_columns = [col for col in column_order if col in df.columns]
        df = df[existing_columns]
        
        return df
    
    def get_analytics(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive analytics from search results"""
        if not articles:
            return {}
        
        analytics = {
            'total_articles': len(articles),
            'with_abstracts': sum(1 for a in articles if a.get('abstract')),
            'with_doi': sum(1 for a in articles if a.get('doi')),
            'with_keywords': sum(1 for a in articles if a.get('keywords')),
            'unique_journals': len(set(a.get('journal', '') for a in articles if a.get('journal'))),
            'unique_authors': len(set(
                author.strip() 
                for article in articles 
                for author in article.get('authors', '').split(',')
                if author.strip()
            )),
            'publication_years': self.extract_years(articles),
            'top_journals': self.get_top_journals(articles),
            'top_authors': self.get_top_authors(articles),
            'keyword_frequency': self.get_keyword_frequency(articles)
        }
        
        return analytics
    
    def extract_years(self, articles: List[Dict[str, Any]]) -> List[int]:
        """Extract publication years from articles"""
        years = []
        for article in articles:
            date_str = article.get('pub_date', '')
            if date_str:
                # Try to extract year (usually last 4 digits)
                year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
                if year_match:
                    years.append(int(year_match.group()))
        return sorted(years)
    
    def get_top_journals(self, articles: List[Dict[str, Any]], top_n: int = 10) -> Dict[str, int]:
        """Get top journals by article count"""
        journal_counts = {}
        for article in articles:
            journal = article.get('journal', '').strip()
            if journal:
                journal_counts[journal] = journal_counts.get(journal, 0) + 1
        
        return dict(sorted(journal_counts.items(), key=lambda x: x[1], reverse=True)[:top_n])
    
    def get_top_authors(self, articles: List[Dict[str, Any]], top_n: int = 10) -> Dict[str, int]:
        """Get top authors by publication count"""
        author_counts = {}
        for article in articles:
            authors_str = article.get('authors', '')
            if authors_str:
                authors = [author.strip() for author in authors_str.split(',')]
                for author in authors:
                    if author and author != 'et al':
                        author_counts[author] = author_counts.get(author, 0) + 1
        
        return dict(sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:top_n])
    
    def get_keyword_frequency(self, articles: List[Dict[str, Any]]) -> Dict[str, int]:
        """Extract and count keyword frequency"""
        keyword_counts = {}
        for article in articles:
            keywords_str = article.get('keywords', '')
            if keywords_str:
                # Handle different keyword formats
                keywords = re.split(r'[,;]', keywords_str)
                for keyword in keywords:
                    keyword = keyword.strip().lower()
                    if keyword and len(keyword) > 2:  # Skip very short terms
                        keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        return dict(sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:20])
    
    def answer_research_question(self, question: str, articles: List[Dict[str, Any]]) -> str:
        """Answer questions about research papers using Ollama"""
        if not OLLAMA_AVAILABLE:
            return "❌ Ollama not available. Please install ollama package."
        
        if not articles:
            return "❌ No research papers available to analyze."
        
        try:
            # Prepare context from articles
            context_parts = []
            for i, article in enumerate(articles[:5]):  # Use top 5 articles
                context = f"""
                Paper {i+1}:
                Title: {article.get('title', 'N/A')}
                Authors: {article.get('authors', 'N/A')}
                Journal: {article.get('journal', 'N/A')}
                Date: {article.get('pub_date', 'N/A')}
                Abstract: {article.get('abstract', 'N/A')}
                Keywords: {article.get('keywords', 'N/A')}
                """
                context_parts.append(context)
            
            full_context = "\n".join(context_parts)
            
            # Create prompt for Ollama
            prompt = f"""
            Based on the following research papers, please answer this question: {question}
            
            Research Papers:
            {full_context}
            
            Please provide a comprehensive answer based on the information available in these papers.
            If the information is not available in the papers, please indicate that.
            """
            
            # Get response from Ollama
            with st.spinner("🤔 Analyzing research papers..."):
                response = ollama.chat(
                    model='llama3.2:1b',  # Use the same model as main app
                    messages=[{'role': 'user', 'content': prompt}]
                )
            
            return response['message']['content']
            
        except Exception as e:
            return f"❌ Error answering question: {e}"
    
    def create_visualizations(self, analytics: Dict[str, Any]):
        """Create interactive visualizations"""
        if not analytics:
            return
        
        viz_tabs = st.tabs(["📅 Timeline", "📰 Journals", "👥 Authors", "🏷️ Keywords", "📊 Overview"])
        
        with viz_tabs[0]:
            st.subheader("Publication Timeline")
            years = analytics.get('publication_years', [])
            if years:
                year_counts = pd.Series(years).value_counts().sort_index()
                
                fig = px.line(
                    x=year_counts.index,
                    y=year_counts.values,
                    title="Publications Over Time",
                    labels={'x': 'Year', 'y': 'Number of Publications'},
                    markers=True
                )
                fig.update_traces(line_color='#1f77b4', marker_size=8)
                st.plotly_chart(fig, use_container_width=True)
                
                # Statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Earliest Publication", min(years))
                with col2:
                    st.metric("Latest Publication", max(years))
                with col3:
                    st.metric("Time Span", f"{max(years) - min(years)} years")
            else:
                st.info("No publication date information available")
        
        with viz_tabs[1]:
            st.subheader("Journal Distribution")
            top_journals = analytics.get('top_journals', {})
            if top_journals:
                # Create bar chart
                fig = px.bar(
                    x=list(top_journals.values()),
                    y=list(top_journals.keys()),
                    orientation='h',
                    title="Top Journals by Publication Count",
                    labels={'x': 'Number of Publications', 'y': 'Journal'}
                )
                fig.update_traces(marker_color='#ff7f0e')
                st.plotly_chart(fig, use_container_width=True)
                
                # Journal table
                st.subheader("Journal Details")
                journal_df = pd.DataFrame([
                    {'Journal': journal, 'Publications': count, 'Percentage': f"{(count/analytics['total_articles']*100):.1f}%"}
                    for journal, count in list(top_journals.items())[:10]
                ])
                st.dataframe(journal_df, use_container_width=True, hide_index=True)
            else:
                st.info("No journal information available")
        
        with viz_tabs[2]:
            st.subheader("Author Analysis")
            top_authors = analytics.get('top_authors', {})
            if top_authors:
                # Create bar chart for top authors
                fig = px.bar(
                    x=list(top_authors.values()),
                    y=list(top_authors.keys()),
                    orientation='h',
                    title="Most Prolific Authors",
                    labels={'x': 'Number of Publications', 'y': 'Author'}
                )
                fig.update_traces(marker_color='#2ca02c')
                st.plotly_chart(fig, use_container_width=True)
                
                # Author details table
                st.subheader("Author Details")
                author_df = pd.DataFrame([
                    {'Author': author, 'Publications': count, 'Share': f"{(count/analytics['total_articles']*100):.1f}%"}
                    for author, count in list(top_authors.items())[:10]
                ])
                st.dataframe(author_df, use_container_width=True, hide_index=True)
            else:
                st.info("No author information available")
        
        with viz_tabs[3]:
            st.subheader("Keyword Analysis")
            keyword_freq = analytics.get('keyword_frequency', {})
            if keyword_freq:
                # Create word cloud style bar chart
                top_keywords = dict(list(keyword_freq.items())[:15])
                fig = px.bar(
                    x=list(top_keywords.values()),
                    y=list(top_keywords.keys()),
                    orientation='h',
                    title="Top Keywords by Frequency",
                    labels={'x': 'Frequency', 'y': 'Keyword'}
                )
                fig.update_traces(marker_color='#9467bd')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No keyword information available")
        
        with viz_tabs[4]:
            st.subheader("Search Overview")
            
            # Create metrics dashboard
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Articles", analytics['total_articles'])
            with col2:
                st.metric("With Abstracts", analytics['with_abstracts'])
            with col3:
                st.metric("Unique Journals", analytics['unique_journals'])
            with col4:
                st.metric("Unique Authors", analytics['unique_authors'])
            
            # Create pie chart for content analysis
            content_data = {
                'With Abstracts': analytics['with_abstracts'],
                'Without Abstracts': analytics['total_articles'] - analytics['with_abstracts']
            }
            
            fig = px.pie(
                values=list(content_data.values()),
                names=list(content_data.keys()),
                title="Abstract Coverage"
            )
            st.plotly_chart(fig, use_container_width=True)

def create_search_interface(hub: EnhancedPubMedHub):
    """Create the main search interface"""
    st.markdown('<div class="search-box">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        query = st.text_input(
            "🔍 Search Query",
            placeholder="e.g., machine learning in cancer diagnosis, COVID-19 vaccines, CRISPR gene editing...",
            help="Use PubMed search syntax. Examples: 'cancer therapy', 'machine learning[Title/Abstract]', 'COVID-19 AND vaccine'"
        )
    
    with col2:
        max_results = st.selectbox(
            "📊 Results",
            options=[10, 20, 50, 100],
            index=1,
            help="Maximum number of articles to retrieve"
        )
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacer
        search_button = st.button("🚀 Search", type="primary", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Search examples
    with st.expander("💡 Search Examples & Tips"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Basic Searches:**")
            st.code("cancer therapy")
            st.code("machine learning")
            st.code("COVID-19 vaccine")
            
            st.markdown("**Field-Specific:**")
            st.code("machine learning[Title/Abstract]")
            st.code("cancer[MeSH Terms]")
        
        with col2:
            st.markdown("**Boolean Operators:**")
            st.code("diabetes OR insulin")
            st.code("cancer NOT leukemia")
            st.code("COVID-19 AND (vaccine OR treatment)")
            
            st.markdown("**Advanced:**")
            st.code("(machine learning OR AI) AND diagnosis[Title/Abstract]")
    
    return query, max_results, search_button

def display_results(hub: EnhancedPubMedHub, articles: List[Dict[str, Any]], df: pd.DataFrame):
    """Display search results with interactive features"""
    if not articles:
        return
    
    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.subheader(f"📄 Search Results ({len(articles)} articles)")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display options
    with st.expander("⚙️ Display Options"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            show_abstracts = st.checkbox("📝 Show Abstracts", value=False)
            show_metadata = st.checkbox("🏷️ Show Metadata", value=True)
        
        with col2:
            available_columns = df.columns.tolist()
            selected_columns = st.multiselect(
                "📋 Select Columns",
                available_columns,
                default=['title', 'authors', 'journal', 'pub_date'],
                help="Choose which columns to display"
            )
        
        with col3:
            sort_by = st.selectbox(
                "🔄 Sort By",
                options=['index', 'title', 'journal', 'pub_date'],
                help="Sort results by selected field"
            )
    
    # Prepare display dataframe
    display_df = df.copy()
    
    # Apply sorting
    if sort_by in display_df.columns:
        display_df = display_df.sort_values(sort_by)
    
    # Apply column selection
    if selected_columns:
        valid_columns = [col for col in selected_columns if col in display_df.columns]
        display_df = display_df[valid_columns]
    
    # Apply display filters
    if not show_abstracts and 'abstract' in display_df.columns:
        display_df = display_df.drop('abstract', axis=1)
    
    if not show_metadata:
        metadata_cols = ['keywords', 'mesh_terms', 'publication_type', 'raw_text']
        display_df = display_df.drop([col for col in metadata_cols if col in display_df.columns], axis=1)
    
    # Display dataframe with custom configuration
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "title": st.column_config.TextColumn("📄 Title", width="large"),
            "authors": st.column_config.TextColumn("👥 Authors", width="medium"),
            "journal": st.column_config.TextColumn("📰 Journal", width="medium"),
            "pub_date": st.column_config.TextColumn("📅 Date", width="small"),
            "pmid": st.column_config.TextColumn("🆔 PMID", width="small"),
            "doi": st.column_config.TextColumn("🔗 DOI", width="medium"),
            "abstract": st.column_config.TextColumn("📝 Abstract", width="large"),
            "keywords": st.column_config.TextColumn("🏷️ Keywords", width="medium"),
            "mesh_terms": st.column_config.TextColumn("🏥 MeSH Terms", width="medium"),
            "publication_type": st.column_config.TextColumn("📋 Type", width="small"),
        }
    )
    
    # Export options
    st.subheader("💾 Export Results")
    
    export_col1, export_col2, export_col3, export_col4 = st.columns(4)
    
    with export_col1:
        if st.button("📥 Download CSV", use_container_width=True):
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📄 CSV File",
                data=csv_data,
                file_name=f"pubmed_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with export_col2:
        if st.button("📥 Download JSON", use_container_width=True):
            json_data = json.dumps(articles, indent=2)
            st.download_button(
                label="📄 JSON File",
                data=json_data,
                file_name=f"pubmed_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with export_col3:
        if st.button("📋 Copy Summary", use_container_width=True):
            summary = df[['title', 'authors', 'journal']].to_string()
            st.code(summary, language="text")
    
    with export_col4:
        if st.button("📊 Export Analytics", use_container_width=True):
            analytics = hub.get_analytics(articles)
            analytics_json = json.dumps(analytics, indent=2)
            st.download_button(
                label="📄 Analytics JSON",
                data=analytics_json,
                file_name=f"pubmed_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

def display_article_details(articles: List[Dict[str, Any]]):
    """Display detailed article view"""
    if not articles:
        return
    
    st.subheader("📖 Article Details")
    
    # Create article selector
    article_options = {
        f"{i+1}: {article.get('title', 'No Title')[:50]}...": i 
        for i, article in enumerate(articles)
    }
    
    selected = st.selectbox(
        "Select Article to View",
        options=list(article_options.keys()),
        help="Choose an article to view detailed information"
    )
    
    if selected:
        article_index = article_options[selected]
        article = articles[article_index]
        
        # Article details card
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        
        # Header
        st.markdown(f"### 📄 Article {article.get('index', 'N/A')}")
        
        # Title and basic info
        st.markdown(f"**📝 Title:** {article.get('title', 'N/A')}")
        st.markdown(f"**👥 Authors:** {article.get('authors', 'N/A')}")
        st.markdown(f"**📰 Journal:** {article.get('journal', 'N/A')}")
        st.markdown(f"**📅 Publication Date:** {article.get('pub_date', 'N/A')}")
        
        # Identifiers
        col1, col2 = st.columns(2)
        with col1:
            if article.get('pmid') and article['pmid'] != 'N/A':
                st.markdown(f"**🆔 PMID:** [{article['pmid']}](https://pubmed.ncbi.nlm.nih.gov/{article['pmid']})")
        
        with col2:
            if article.get('doi') and article['doi'] != 'N/A':
                st.markdown(f"**🔗 DOI:** [{article['doi']}](https://doi.org/{article['doi']})")
        
        # Abstract with scrollable text
        if article.get('abstract') and article['abstract'] != 'N/A':
            st.markdown("**📝 Abstract:**")
            st.markdown(
                f'<div class="abstract-text">{article.get("abstract", "")}</div>',
                unsafe_allow_html=True
            )
        
        # Additional metadata
        metadata_expander = st.expander("🏷️ Additional Metadata")
        with metadata_expander:
            if article.get('keywords') and article['keywords'] != 'N/A':
                st.markdown(f"**🏷️ Keywords:** {article['keywords']}")
            
            if article.get('mesh_terms') and article['mesh_terms'] != 'N/A':
                st.markdown(f"**🏥 MeSH Terms:** {article['mesh_terms']}")
            
            if article.get('publication_type') and article['publication_type'] != 'N/A':
                st.markdown(f"**📋 Publication Type:** {article['publication_type']}")
            
            if article.get('copyright') and article['copyright'] != 'N/A':
                st.markdown(f"**©️ Copyright:** {article['copyright']}")
        
        # Full text with scrollable area
        if article.get('full_text') and article['full_text'] != 'N/A':
            if st.checkbox("📄 Show Full Text"):
                st.markdown("**📄 Full Text:**")
                st.markdown(
                    f'<div class="scrollable-text">{article.get("full_text", "")}</div>',
                    unsafe_allow_html=True
                )
        
        # Raw text option
        if st.checkbox("📄 Show Raw Parsed Text"):
            st.code(article.get('raw_text', 'No raw text available'), language="text")
        
        st.markdown('</div>', unsafe_allow_html=True)

def display_research_qa(hub: EnhancedPubMedHub, articles: List[Dict[str, Any]]):
    """Display Q&A interface for research papers"""
    if not articles:
        return
    
    st.markdown('<div class="qa-container">', unsafe_allow_html=True)
    st.subheader("🤔 Research Paper Q&A")
    st.markdown("Ask questions about the research papers found in your search.")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Q&A interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        question = st.text_input(
            "💬 Ask a question about these research papers:",
            placeholder="e.g., What are the main findings about cancer treatment? What methodologies were used?",
            help="Ask any question about the research papers in your search results"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacer
        ask_button = st.button("🤔 Ask", type="primary", use_container_width=True)
    
    if ask_button and question:
        if not OLLAMA_AVAILABLE:
            st.error("❌ Ollama not available. Please install ollama package and ensure Ollama is running.")
            st.info("💡 Install with: pip install ollama")
            st.info("🚀 Start Ollama: ollama serve")
        else:
            # Check if Ollama is running
            try:
                models = ollama.list()
                if not models.get('models'):
                    st.error("❌ No Ollama models found. Please pull a model:")
                    st.code("ollama pull llama3.2:1b")
                else:
                    # Answer the question
                    answer = hub.answer_research_question(question, articles)
                    st.markdown('<div class="qa-container">', unsafe_allow_html=True)
                    st.markdown("### 🤖 Answer:")
                    st.markdown(answer)
                    st.markdown('</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"❌ Error connecting to Ollama: {e}")
                st.info("💡 Make sure Ollama is running: ollama serve")

def main():
    """Main application"""
    # Header
    st.markdown('<h1 class="main-header">🔬 Enhanced PubMed Research Hub</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666; margin-bottom: 2rem;">Advanced Biomedical Literature Search with Q&A Capabilities</p>', unsafe_allow_html=True)
    
    # Check PubMed availability
    if not PUBMED_AVAILABLE:
        st.error("❌ PubMed libraries not available. Please install:")
        st.code("pip install langchain-community biopython")
        st.stop()
    
    # Initialize research hub
    if 'enhanced_pubmed_hub' not in st.session_state:
        st.session_state.enhanced_pubmed_hub = EnhancedPubMedHub()
    
    hub = st.session_state.enhanced_pubmed_hub
    
    # Sidebar
    with st.sidebar:
        st.header("🔬 Enhanced PubMed")
        
        st.markdown("---")
        st.markdown("**📊 Quick Stats:**")
        if 'enhanced_search_history' in st.session_state and st.session_state.enhanced_search_history:
            total_searches = len(st.session_state.enhanced_search_history)
            total_articles = sum(h['count'] for h in st.session_state.enhanced_search_history)
            st.metric("Total Searches", total_searches)
            st.metric("Articles Found", total_articles)
        else:
            st.metric("Total Searches", 0)
            st.metric("Articles Found", 0)
        
        st.markdown("---")
        st.markdown("**🤖 Q&A Status:**")
        if OLLAMA_AVAILABLE:
            try:
                models = ollama.list()
                if models.get('models'):
                    st.success("✅ Ollama Ready")
                    st.info(f"📦 Models: {len(models['models'])} available")
                else:
                    st.warning("⚠️ No Ollama models")
                    st.info("💡 Run: ollama pull llama3.2:1b")
            except:
                st.error("❌ Ollama not running")
                st.info("💡 Run: ollama serve")
        else:
            st.error("❌ Ollama not installed")
            st.info("💡 Install: pip install ollama")
        
        st.markdown("---")
        st.markdown("**🔧 Settings:**")
        
        email = st.text_input(
            "📧 Email (for PubMed API)",
            value="researcher@example.com",
            help="Required by PubMed API for usage tracking"
        )
        
        if st.button("🔄 Update Settings"):
            if hub.api_wrapper:
                hub.api_wrapper.email = email
                st.success("✅ Settings updated!")
                st.rerun()
        
        st.markdown("---")
        st.markdown("**📚 Resources:**")
        st.markdown("- [PubMed Help](https://pubmed.ncbi.nlm.nih.gov/help/)")
        st.markdown("- [Search Syntax](https://pubmed.ncbi.nlm.nih.gov/help/)")
        st.markdown("- [NCBI APIs](https://www.ncbi.nlm.nih.gov/books/NBK25501/)")
    
    # Main content area
    # Search interface
    query, max_results, search_button = create_search_interface(hub)
    
    # Search execution
    if search_button and query:
        # Store search in history
        if 'enhanced_search_history' not in st.session_state:
            st.session_state.enhanced_search_history = []
        
        # Perform search
        articles = hub.search_literature(query, max_results)
        
        if articles:
            # Update history
            st.session_state.enhanced_search_history.append({
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'count': len(articles)
            })
            
            # Create dataframe
            df = hub.create_dataframe(articles)
            
            # Store in session state
            st.session_state.current_articles = articles
            st.session_state.current_dataframe = df
            st.session_state.current_analytics = hub.get_analytics(articles)
            
            # Success message
            st.success(f"✅ Found {len(articles)} articles for '{query}'")
        else:
            st.warning("⚠️ No results found or search failed")
    
    # Display results if available
    if 'current_articles' in st.session_state and st.session_state.current_articles:
        articles = st.session_state.current_articles
        df = st.session_state.current_dataframe
        analytics = st.session_state.current_analytics
        
        # Results display
        display_results(hub, articles, df)
        
        # Analytics
        st.markdown("---")
        hub.create_visualizations(analytics)
        
        # Article details
        st.markdown("---")
        display_article_details(articles)
        
        # Q&A Section
        st.markdown("---")
        display_research_qa(hub, articles)
    
    # Search history
    if 'enhanced_search_history' in st.session_state and st.session_state.enhanced_search_history:
        st.markdown("---")
        st.subheader("📜 Search History")
        
        history_df = pd.DataFrame(st.session_state.enhanced_search_history)
        history_df['timestamp'] = pd.to_datetime(history_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        
        st.dataframe(
            history_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "query": st.column_config.TextColumn("🔍 Query", width="large"),
                "timestamp": st.column_config.TextColumn("⏰ Time", width="medium"),
                "count": st.column_config.NumberColumn("📊 Results", width="small")
            }
        )
        
        if st.button("🗑️ Clear History"):
            st.session_state.enhanced_search_history = []
            st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 2rem 0;'>
            <p>🔬 <strong>Enhanced PubMed Research Hub</strong> - Advanced Biomedical Literature Search with Q&A</p>
            <p>Powered by LangChain • Data from PubMed® • 35+ Million Citations • Enhanced with Ollama Q&A</p>
            <p><em>PubMed® is a registered trademark of the U.S. National Library of Medicine</em></p>
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
