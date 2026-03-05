# 🔬 PubMed Search Integration

Advanced biomedical literature search powered by LangChain's PubMed integration with interactive dataframe preview and analytics.

## ✨ Features

### 🔍 **Advanced Search Capabilities**
- **PubMed API Integration** - Direct access to 35+ million biomedical citations
- **Flexible Query Syntax** - Support for PubMed search operators and filters
- **Configurable Results** - Adjustable result limits from 5 to 100 articles
- **Real-time Search** - Fast, responsive search with progress indicators

### 📊 **Dataframe Preview & Analytics**
- **Interactive Dataframe** - Sortable, filterable results table
- **Column Selection** - Choose which data fields to display
- **Export Options** - Download results as CSV or JSON
- **Search Statistics** - Automatic analysis of search results

### 📈 **Visual Analytics**
- **Publication Timeline** - Year-wise distribution of articles
- **Journal Distribution** - Top journals pie chart visualization
- **Author Network** - Most prolific authors analysis
- **Interactive Charts** - Powered by Plotly for dynamic exploration

### 📄 **Detailed Article View**
- **Article Details** - Complete metadata for each publication
- **Abstract Preview** - Full abstract text with formatting
- **External Links** - Direct links to PubMed and DOI URLs
- **Raw Text Access** - Complete parsed article data

## 🚀 Quick Start

### Installation
```bash
# Install required packages
pip install streamlit pandas plotly langchain-community xmltodict

# Or update requirements
pip install -r requirements.txt
```

### Launch PubMed Search
```bash
# Using the launcher script
./run_pubmed.sh

# Or directly with Streamlit
streamlit run pubmed_search.py --server.port=8503
```

### Access
- **URL**: http://localhost:8503
- **Default Port**: 8503 (customizable)
- **No API Keys Required**: Uses free public PubMed API

## 🔧 Usage Guide

### Basic Search
1. **Enter Query**: Type your search terms in the search box
2. **Set Results**: Choose maximum number of articles (5-100)
3. **Click Search**: Execute the PubMed search
4. **View Results**: Browse the interactive dataframe

### Advanced Search Syntax
```text
# Basic terms
cancer therapy
machine learning

# Field-specific search
machine learning[Title/Abstract]
COVID-19 AND vaccine
CRISPR[Title] AND gene editing

# Boolean operators
diabetes OR insulin
cancer NOT leukemia
("machine learning" OR "artificial intelligence") AND diagnosis
```

### Dataframe Features
- **Column Selection**: Choose which columns to display
- **Show/Hide Abstracts**: Toggle abstract text visibility
- **Raw Text Access**: View complete parsed article data
- **Sort & Filter**: Built-in dataframe operations

### Export Options
- **CSV Export**: Structured data for spreadsheet analysis
- **JSON Export**: Complete article metadata in JSON format
- **Clipboard Copy**: Quick copy of tabular data

## 📊 Analytics Dashboard

### Publication Timeline
- **Year-wise Distribution**: Visualize publication trends over time
- **Interactive Bar Chart**: Click bars for detailed information
- **Date Range Analysis**: Automatic extraction from publication dates

### Journal Distribution
- **Top 10 Journals**: Pie chart showing most frequent journals
- **Percentage Breakdown**: Relative contribution of each journal
- **Publication Venues**: Identify key research outlets

### Author Network
- **Prolific Authors**: Top 10 most published authors
- **Publication Count**: Number of articles per author
- **Collaboration Insights**: Potential collaboration opportunities

## 🛠️ Technical Implementation

### LangChain Integration
```python
from langchain_community.utilities.pubmed import PubMedAPIWrapper

# Initialize PubMed wrapper (no API key needed!)
api_wrapper = PubMedAPIWrapper(
    top_k_results=20,
    email="researcher@example.com"  # Just for identification
)
```

### Data Processing Pipeline
1. **Query Execution** - PubMed API call with search terms
2. **Result Parsing** - Structured extraction of article metadata
3. **Dataframe Creation** - Pandas DataFrame for tabular display
4. **Analytics Generation** - Statistical analysis and visualization
5. **Export Formatting** - CSV/JSON output preparation

### Error Handling
- **API Failures** - Graceful handling of PubMed API errors
- **Parse Errors** - Fallback to raw text display
- **Network Issues** - Retry mechanisms and user notifications
- **Data Validation** - Type checking and data cleaning

## 📋 Data Fields

### Core Metadata
- **Title** - Article title
- **Authors** - Author list with full names
- **Journal** - Publication journal name
- **Publication Date** - Release date information
- **PMID** - PubMed unique identifier
- **DOI** - Digital Object Identifier
- **Abstract** - Article abstract text

### Extended Fields
- **Raw Text** - Complete parsed article data
- **Index** - Result position in search
- **Query Context** - Search terms used

## 🔍 Search Tips

### Effective Queries
- **Be Specific**: Use precise terminology for better results
- **Use Filters**: Apply field-specific searches when possible
- **Combine Terms**: Use Boolean operators for complex queries
- **Check Synonyms**: Try alternative terminology

### Search Optimization
- **Result Limits**: Start with smaller limits for faster searches
- **Field Specificity**: Use [Title/Abstract] for targeted searches
- **Date Ranges**: Include year ranges for temporal filtering
- **Journal Names**: Specify journals for focused searches

## 🚨 Limitations & Considerations

### API Limitations
- **Rate Limits**: PubMed API has usage restrictions (~3 requests/second)
- **Result Caps**: Maximum 100 results per search
- **Update Delays**: Recent articles may not be immediately available
- **No API Key Required**: Free public access to all features

### Data Quality
- **Parsing Variability**: Article format may affect parsing
- **Missing Fields**: Some articles may lack complete metadata
- **Abstract Availability**: Not all articles include abstracts

### Performance Considerations
- **Large Result Sets**: More results = longer processing time
- **Complex Queries**: Detailed searches may take longer
- **Visualization Limits**: Charts may be slow with large datasets

## 🔄 Integration with Main App

### Adding to Main Application
```python
# In app.py, add to sidebar
if st.sidebar.button("🔬 PubMed Search"):
    st.switch_page("pubmed_search.py")
```

### Shared Components
- **Session State**: Share search history across pages
- **User Preferences**: Common settings and configurations
- **Data Export**: Unified download functionality

## 📚 Additional Resources

### PubMed Documentation
- **PubMed API**: https://www.ncbi.nlm.nih.gov/books/NBK25501/
- **Search Syntax**: https://www.ncbi.nlm.nih.gov/pubmed/advanced/
- **API Guidelines**: https://www.ncbi.nlm.nih.gov/pmc/tools/oai/

### LangChain Integration
- **PubMed Tools**: https://python.langchain.com/docs/integrations/tools/pubmed/
- **API Wrapper**: https://api.python.langchain.com/en/latest/utilities/langchain_community.utilities.pubmed.PubMedAPIWrapper.html

### Biomedical Research
- **NCBI Resources**: https://www.ncbi.nlm.nih.gov/
- **PubMed Central**: https://www.ncbi.nlm.nih.gov/pmc/
- **MEDLINE Database**: https://www.nlm.nih.gov/databases/

## 🤝 Contributing

### Adding Features
- **New Visualizations**: Additional chart types and analytics
- **Export Formats**: Support for BibTeX, RIS, etc.
- **Search Filters**: Advanced filtering options
- **Batch Operations**: Multiple query processing

### Code Structure
- **Modular Design**: Separate search, parsing, and visualization
- **Error Handling**: Comprehensive exception management
- **Testing**: Unit tests for core functionality
- **Documentation**: Inline comments and docstrings

---

🔬 **Ready for biomedical research exploration!** Start searching PubMed with advanced analytics and dataframe capabilities.
