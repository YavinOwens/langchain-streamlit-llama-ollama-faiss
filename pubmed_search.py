"""
PubMed Search Interface - Advanced Biomedical Literature Search
Utilizes LangChain's PubMed integration with dataframe preview capabilities
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Try to import PubMed utilities
try:
    from langchain_community.utilities.pubmed import PubMedAPIWrapper
    PUBMED_AVAILABLE = True
except ImportError:
    PUBMED_AVAILABLE = False
    st.warning("⚠️ PubMed libraries not available. Please install: pip install langchain-community")

# Initialize session state
if 'pubmed_history' not in st.session_state:
    st.session_state.pubmed_history = []
if 'pubmed_results' not in st.session_state:
    st.session_state.pubmed_results = []
if 'pubmed_dataframe' not in st.session_state:
    st.session_state.pubmed_dataframe = pd.DataFrame()

class PubMedSearcher:
    """Advanced PubMed search with dataframe capabilities"""
    
    def __init__(self):
        self.api_wrapper = None
        self.last_query = ""
        self.last_results = []
        
        if PUBMED_AVAILABLE:
            try:
                # Initialize PubMed API wrapper
                self.api_wrapper = PubMedAPIWrapper(
                    top_k_results=20,  # Default number of results
                    email="researcher@example.com"  # Required by PubMed API for identification
                )
                
            except Exception as e:
                # Only show error if running in Streamlit
                try:
                    st.error(f"Failed to initialize PubMed: {e}")
                except:
                    print(f"Failed to initialize PubMed: {e}")
    
    def search_pubmed(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """Search PubMed and return structured results"""
        if not PUBMED_AVAILABLE or not self.api_wrapper:
            st.error("PubMed not available")
            return []
        
        try:
            # Update top_k_results if needed
            if max_results != self.api_wrapper.top_k_results:
                self.api_wrapper.top_k_results = max_results
            
            # Perform search
            with st.spinner(f"🔍 Searching PubMed for: '{query}'..."):
                results = self.api_wrapper.run(query)
                
            # Parse results into structured format
            parsed_results = self._parse_pubmed_results(results)
            
            self.last_query = query
            self.last_results = parsed_results
            
            return parsed_results
            
        except Exception as e:
            st.error(f"Search failed: {e}")
            return []
    
    def _parse_pubmed_results(self, results: str) -> List[Dict[str, Any]]:
        """Parse PubMed results into structured format"""
        parsed_results = []
        
        try:
            # Split results by article (assuming each article is separated by newlines)
            articles = results.split('\n\n')
            
            for i, article in enumerate(articles):
                if article.strip():
                    parsed_article = self._parse_single_article(article, i+1)
                    if parsed_article:
                        parsed_results.append(parsed_article)
                        
        except Exception as e:
            st.error(f"Error parsing results: {e}")
            # Return raw results as single entry
            parsed_results.append({
                'index': 1,
                'title': 'Parse Error',
                'authors': 'N/A',
                'journal': 'N/A',
                'pub_date': 'N/A',
                'pmid': 'N/A',
                'abstract': results[:500] + '...' if len(results) > 500 else results,
                'doi': 'N/A',
                'raw_text': article
            })
        
        return parsed_results
    
    def _parse_single_article(self, article_text: str, index: int) -> Optional[Dict[str, Any]]:
        """Parse a single article from PubMed results"""
        lines = article_text.split('\n')
        article = {
            'index': index,
            'title': '',
            'authors': '',
            'journal': '',
            'pub_date': '',
            'pmid': '',
            'abstract': '',
            'doi': '',
            'raw_text': article_text
        }
        
        current_field = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            line_lower = line.lower()
            
            if line_lower.startswith('title:') or line_lower.startswith('article:'):
                current_field = 'title'
                article['title'] = line.split(':', 1)[1].strip()
            elif line_lower.startswith('author') or line_lower.startswith('authors:'):
                current_field = 'authors'
                article['authors'] = line.split(':', 1)[1].strip()
            elif line_lower.startswith('journal') or line_lower.startswith('source:'):
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
            else:
                # Continue with current field
                if current_field and current_field in article:
                    article[current_field] += ' ' + line
        
        # Extract title if not found (often first line)
        if not article['title'] and lines:
            article['title'] = lines[0].strip()
        
        return article if article['title'] or article['abstract'] else None
    
    def create_dataframe(self, results: List[Dict[str, Any]]) -> pd.DataFrame:
        """Convert results to pandas DataFrame"""
        if not results:
            return pd.DataFrame()
        
        df = pd.DataFrame(results)
        
        # Reorder columns for better display
        columns_order = ['index', 'title', 'authors', 'journal', 'pub_date', 'pmid', 'doi', 'abstract']
        existing_columns = [col for col in columns_order if col in df.columns]
        df = df[existing_columns]
        
        return df
    
    def get_search_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about search results"""
        if not results:
            return {}
        
        stats = {
            'total_articles': len(results),
            'with_abstract': sum(1 for r in results if r.get('abstract')),
            'with_doi': sum(1 for r in results if r.get('doi')),
            'journals': len(set(r.get('journal', '') for r in results if r.get('journal'))),
            'date_range': self._get_date_range(results)
        }
        
        return stats
    
    def _get_date_range(self, results: List[Dict[str, Any]]) -> str:
        """Extract date range from results"""
        dates = []
        for result in results:
            date_str = result.get('pub_date', '')
            if date_str:
                try:
                    # Try to extract year from date string
                    year = int(date_str.split()[-1])
                    dates.append(year)
                except:
                    pass
        
        if dates:
            return f"{min(dates)} - {max(dates)}"
        return "Unknown"

def create_visualizations(results: List[Dict[str, Any]], df: pd.DataFrame):
    """Create visualizations for PubMed results"""
    if not results or df.empty:
        return
    
    st.subheader("📊 Search Analytics")
    
    # Create tabs for different visualizations
    viz_tabs = st.tabs(["Publication Timeline", "Journal Distribution", "Author Network"])
    
    with viz_tabs[0]:
        # Publication timeline
        years = []
        for result in results:
            date_str = result.get('pub_date', '')
            if date_str:
                try:
                    year = int(date_str.split()[-1])
                    years.append(year)
                except:
                    pass
        
        if years:
            year_counts = pd.Series(years).value_counts().sort_index()
            fig = px.bar(
                x=year_counts.index, 
                y=year_counts.values,
                title="Publications by Year",
                labels={'x': 'Year', 'y': 'Number of Publications'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No date information available for timeline visualization")
    
    with viz_tabs[1]:
        # Journal distribution
        journals = df['journal'].value_counts().head(10)
        if not journals.empty:
            fig = px.pie(
                values=journals.values,
                names=journals.index,
                title="Top 10 Journals"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No journal information available")
    
    with viz_tabs[2]:
        # Author statistics
        all_authors = []
        for result in results:
            authors = result.get('authors', '')
            if authors:
                # Split authors and clean up
                author_list = [author.strip() for author in authors.split(',')]
                all_authors.extend(author_list)
        
        if all_authors:
            author_counts = pd.Series(all_authors).value_counts().head(10)
            st.write("**Top 10 Most Prolific Authors:**")
            for i, (author, count) in enumerate(author_counts.items(), 1):
                st.write(f"{i}. {author}: {count} publications")
        else:
            st.info("No author information available")

def main():
    """Main PubMed search interface"""
    st.set_page_config(
        page_title="PubMed Search",
        page_icon="🔬",
        layout="wide"
    )
    
    # Header
    st.title("🔬 PubMed Literature Search")
    st.markdown("*Advanced biomedical literature search with LangChain integration*")
    
    if not PUBMED_AVAILABLE:
        st.error("❌ PubMed libraries not installed. Please run:")
        st.code("pip install langchain-community")
        st.stop()
    
    # Initialize searcher
    if 'pubmed_searcher' not in st.session_state:
        st.session_state.pubmed_searcher = PubMedSearcher()
    
    searcher = st.session_state.pubmed_searcher
    
    # Search interface
    st.subheader("🔍 Search Configuration")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        query = st.text_input(
            "Search Query",
            placeholder="e.g., machine learning in cancer diagnosis, COVID-19 vaccines, CRISPR gene editing...",
            help="Use PubMed search syntax. Examples: 'cancer therapy', 'machine learning[Title/Abstract]', 'COVID-19 AND vaccine'"
        )
    
    with col2:
        max_results = st.number_input(
            "Max Results",
            min_value=5,
            max_value=100,
            value=20,
            step=5,
            help="Maximum number of articles to retrieve"
        )
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacer
        search_button = st.button("🔍 Search", type="primary")
    
    # Search execution
    if search_button and query:
        results = searcher.search_pubmed(query, max_results)
        
        if results:
            st.session_state.pubmed_results = results
            st.session_state.pubmed_dataframe = searcher.create_dataframe(results)
            st.session_state.pubmed_history.append({
                'query': query,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'results_count': len(results)
            })
        else:
            st.warning("No results found or search failed")
    
    # Display results
    if st.session_state.pubmed_results:
        results = st.session_state.pubmed_results
        df = st.session_state.pubmed_dataframe
        
        st.subheader(f"📄 Search Results ({len(results)} articles)")
        
        # Statistics
        stats = searcher.get_search_statistics(results)
        if stats:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Articles", stats['total_articles'])
            with col2:
                st.metric("With Abstracts", stats['with_abstract'])
            with col3:
                st.metric("Unique Journals", stats['journals'])
            with col4:
                st.metric("Date Range", stats['date_range'])
        
        # Dataframe display
        st.subheader("📊 Results Table")
        
        # Display options
        display_col1, display_col2 = st.columns([1, 1])
        
        with display_col1:
            show_abstracts = st.checkbox("Show Abstracts", value=False)
            show_raw = st.checkbox("Show Raw Text", value=False)
        
        with display_col2:
            # Column selection
            available_columns = df.columns.tolist()
            selected_columns = st.multiselect(
                "Select Columns to Display",
                available_columns,
                default=['title', 'authors', 'journal', 'pub_date'],
                help="Choose which columns to display in the table"
            )
        
        # Filter dataframe
        display_df = df.copy()
        
        if not show_abstracts and 'abstract' in display_df.columns:
            display_df = display_df.drop('abstract', axis=1)
        
        if not show_raw and 'raw_text' in display_df.columns:
            display_df = display_df.drop('raw_text', axis=1)
        
        if selected_columns:
            # Ensure selected columns exist
            valid_columns = [col for col in selected_columns if col in display_df.columns]
            display_df = display_df[valid_columns]
        
        # Display dataframe
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "title": st.column_config.TextColumn("Title", width="large"),
                "authors": st.column_config.TextColumn("Authors", width="medium"),
                "journal": st.column_config.TextColumn("Journal", width="medium"),
                "pub_date": st.column_config.TextColumn("Publication Date", width="small"),
                "pmid": st.column_config.TextColumn("PMID", width="small"),
                "doi": st.column_config.TextColumn("DOI", width="medium"),
                "abstract": st.column_config.TextColumn("Abstract", width="large"),
            }
        )
        
        # Download options
        st.subheader("💾 Export Options")
        
        export_col1, export_col2, export_col3 = st.columns(3)
        
        with export_col1:
            if st.button("📥 Download CSV"):
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="Download PubMed Results",
                    data=csv_data,
                    file_name=f"pubmed_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with export_col2:
            if st.button("📥 Download JSON"):
                json_data = json.dumps(results, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name=f"pubmed_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with export_col3:
            if st.button("📋 Copy to Clipboard"):
                st.code(df.to_string(), language="text")
        
        # Visualizations
        create_visualizations(results, df)
        
        # Detailed article view
        st.subheader("📖 Detailed Article View")
        
        if not df.empty:
            selected_article = st.selectbox(
                "Select Article for Details",
                options=df.index,
                format_func=lambda x: f"{df.loc[x, 'index']}: {df.loc[x, 'title'][:50]}..." if len(df.loc[x, 'title']) > 50 else df.loc[x, 'title']
            )
            
            if selected_article is not None:
                article_data = df.loc[selected_article]
                
                st.markdown("---")
                st.markdown(f"### 📄 Article {article_data.get('index', 'N/A')}")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Title:** {article_data.get('title', 'N/A')}")
                    st.markdown(f"**Authors:** {article_data.get('authors', 'N/A')}")
                    st.markdown(f"**Journal:** {article_data.get('journal', 'N/A')}")
                    st.markdown(f"**Publication Date:** {article_data.get('pub_date', 'N/A')}")
                    
                    if article_data.get('doi') and article_data['doi'] != 'N/A':
                        st.markdown(f"**DOI:** [{article_data['doi']}](https://doi.org/{article_data['doi']})")
                    
                    if article_data.get('pmid') and article_data['pmid'] != 'N/A':
                        st.markdown(f"**PMID:** [{article_data['pmid']}](https://pubmed.ncbi.nlm.nih.gov/{article_data['pmid']})")
                
                with col2:
                    if st.button("🔗 Open in PubMed"):
                        pmid = article_data.get('pmid', '')
                        if pmid and pmid != 'N/A':
                            st.markdown(f"[Open in PubMed](https://pubmed.ncbi.nlm.nih.gov/{pmid})")
                
                if article_data.get('abstract') and article_data['abstract'] != 'N/A':
                    st.markdown("**Abstract:**")
                    st.markdown(article_data['abstract'])
                
                if show_raw and article_data.get('raw_text'):
                    st.markdown("**Raw Text:**")
                    st.code(article_data['raw_text'])
    
    # Search history
    if st.session_state.pubmed_history:
        st.subheader("📜 Search History")
        
        history_df = pd.DataFrame(st.session_state.pubmed_history)
        st.dataframe(
            history_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "query": st.column_config.TextColumn("Query", width="large"),
                "timestamp": st.column_config.TextColumn("Time", width="medium"),
                "results_count": st.column_config.NumberColumn("Results", width="small")
            }
        )
        
        if st.button("🗑️ Clear History"):
            st.session_state.pubmed_history = []
            st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        **About:** This PubMed search interface uses LangChain's PubMed integration to provide 
        advanced biomedical literature search capabilities with dataframe preview and analytics.
        
        **Data Source:** PubMed® by The National Center for Biotechnology Information, 
        National Library of Medicine contains more than 35 million citations for biomedical literature.
        """
    )

if __name__ == "__main__":
    main()
