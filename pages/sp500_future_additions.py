import streamlit as st
import pandas as pd
import plotly.express as px
from utils.sp400_analyzer import Russell1000Analyzer

# Configure page
st.set_page_config(page_title="S&P 500 Future Additions - Trade Ideas", page_icon="🔮", layout="wide")

st.title("🔮 S&P 500 Future Additions Analysis")
st.markdown("Russell 1000 companies (excluding current S&P 500) most likely to be promoted to the S&P 500")

# Load and analyze Russell 1000 data
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_russell_analysis():
    """Load Russell 1000 companies, filter out S&P 500, and analyze for S&P 500 inclusion likelihood"""
    try:
        analyzer = Russell1000Analyzer()
        # Get S&P 500 candidates from Russell 1000 (filtered automatically)
        candidates = analyzer.get_sp500_candidates(max_companies=1000)
        return candidates
    except Exception as e:
        st.error(f"Error analyzing Russell 1000 candidates: {str(e)}")
        return pd.DataFrame()

with st.spinner("Analyzing Russell 1000 companies for S&P 500 promotion likelihood..."):
    candidates_df = load_russell_analysis()

if not candidates_df.empty:
    st.subheader("🏆 Top Candidates for S&P 500 Inclusion")

    # Display inclusion criteria
    with st.expander("📋 S&P 500 Inclusion Criteria"):
        st.markdown("""
        **Current Requirements (2025):**
        - **Market Cap**: Minimum $22.7 billion
        - **Profitability**: Positive GAAP earnings (recent quarter + trailing 4 quarters)
        - **Float**: At least 50% of shares publicly traded
        - **Liquidity**: 250,000 shares/month for 6 months + liquidity ratio ≥ 0.75
        - **Location**: US-based company on major US exchange
        - **Committee Approval**: Final discretionary review by S&P Index Committee
        """)

    # Top candidates table with column selector
    top_candidates = candidates_df

    # Column mapping for user-friendly names
    column_mapping = {
        'Symbol': 'Symbol',
        'Company': 'Company',
        'Sector': 'GICS_Sector',
        'Market Cap ($B)': 'Market_Cap_B',
        'Revenue Growth (%)': 'Revenue_Growth_TTM',
        'Profit Margin (%)': 'Profit_Margin',
        'ROE (%)': 'ROE',
        'Score': 'Inclusion_Score',
        'Meets Criteria': 'criteria_met'
    }

    # Column selector
    available_columns = list(column_mapping.keys())
    selected_columns = st.multiselect(
        "Select columns to display:",
        options=available_columns,
        default=available_columns,
        key="column_selector"
    )

    top_candidates = top_candidates[top_candidates["criteria_met"]]

    if selected_columns:
        # Map selected display names back to actual column names
        actual_cols = [column_mapping[col] for col in selected_columns]
        display_df = top_candidates[actual_cols].copy()
        display_df.columns = selected_columns

        # Format numerical columns if they're selected
        if 'Market Cap ($B)' in display_df.columns:
            display_df['Market Cap ($B)'] = display_df['Market Cap ($B)'].round(1)
        if 'Revenue Growth (%)' in display_df.columns:
            display_df['Revenue Growth (%)'] = display_df['Revenue Growth (%)'].round(1)
        if 'Profit Margin (%)' in display_df.columns:
            display_df['Profit Margin (%)'] = display_df['Profit Margin (%)'].round(1)
        if 'ROE (%)' in display_df.columns:
            display_df['ROE (%)'] = display_df['ROE (%)'].round(1)
        if 'Score' in display_df.columns:
            display_df['Score'] = display_df['Score'].round(1)

        st.dataframe(display_df,
                     width='stretch',
                     height = (len(display_df)+1)*35,
                     hide_index=True)
    else:
        st.warning("Please select at least one column to display.")

    # Create visualization of top candidates
    fig = px.scatter(
        top_candidates.head(20),
        x='Market_Cap_B',
        y='Inclusion_Score',
        color='GICS_Sector',
        size='Average_Volume_M',
        hover_data=['Company', 'Revenue_Growth_TTM', 'Profit_Margin'],
        title="Russell 1000 Companies: Market Cap vs. Inclusion Score",
        labels={
            'Market_Cap_B': 'Market Cap ($ Billions)',
            'Inclusion_Score': 'S&P 500 Inclusion Score',
            'Average_Volume_M': 'Avg Volume (Millions)'
        }
    )

    # Add threshold line for S&P 500 market cap requirement
    fig.add_hline(
        y=70,
        line_dash="dash",
        line_color="green",
        annotation_text="Strong Inclusion Likelihood (Score ≥ 70)"
    )

    fig.add_vline(
        x=22.7,
        line_dash="dash",
        line_color="red",
        annotation_text="S&P 500 Min Market Cap ($22.7B)"
    )

    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Unable to load S&P 400 analysis data. Please try again later.")

# Additional information
with st.expander("ℹ️ About this Analysis"):
    st.markdown("""
    **Data Sources:**
    - Russell 1000 company data: Wikipedia
    - S&P 500 company data: Wikipedia (for filtering)
    - Financial metrics: Yahoo Finance (yfinance)
    - Inclusion scoring: Based on official S&P 500 criteria

    **Methodology:**
    - Russell 1000 companies already in S&P 500 are filtered out automatically
    - Inclusion scores consider market cap, profitability, growth, financial health, and liquidity
    - Scores range from 0-100, with 70+ indicating strong inclusion likelihood

    **Notes:**
    - Future inclusion predictions are based on quantitative analysis only
    - Final S&P 500 inclusion is at the discretion of the S&P Index Committee
    """)
