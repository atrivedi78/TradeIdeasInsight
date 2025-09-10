import streamlit as st

# Configure the page
st.set_page_config(
    page_title="Trade Ideas",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main page content
st.title("📈 Trade Ideas")
st.markdown("""
Welcome to Trade Ideas - your comprehensive financial analysis platform.

## Available Analysis Tools

### 📊 S&P 500 Additions
Analyze historical S&P 500 additions and removals with performance tracking.
- Historical data from Wikipedia
- Interactive date selection
- Performance analysis 3 months before/after announcements
- Price data rebased to announcement dates

Navigate to the **S&P 500 Additions** page using the sidebar to get started.
""")

# Sidebar navigation info
with st.sidebar:
    st.markdown("## Navigation")
    st.markdown("Use the pages above to navigate between different analysis tools.")
    
    st.markdown("## About")
    st.markdown("""
    Trade Ideas provides comprehensive financial analysis tools for:
    - S&P 500 historical changes
    - Stock performance tracking
    - Market event analysis
    """)
