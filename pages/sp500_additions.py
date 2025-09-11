import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
from typing import Any
from utils.data_scraper import SP500DataScraper
from utils.stock_analysis import StockAnalyzer
from utils.sp400_analyzer import Russell1000Analyzer

# Configure page
st.set_page_config(page_title="S&P 500 Additions - Trade Ideas", page_icon="📊", layout="wide")

st.title("📊 S&P 500 Additions & Removals Analysis")
st.markdown("Historical analysis of S&P 500 changes with performance tracking")

# Initialize components
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_sp500_changes():
    """Load S&P 500 historical changes data"""
    try:
        scraper = SP500DataScraper()
        changes_data = scraper.get_historical_changes()
        return changes_data
    except Exception as e:
        st.error(f"Error loading S&P 500 data: {str(e)}")
        return pd.DataFrame()

# Load data
with st.spinner("Loading S&P 500 historical data..."):
    changes_df = load_sp500_changes()

if changes_df.empty:
    st.error("Unable to load S&P 500 historical data. Please try again later.")
    st.stop()

# Date selection section
st.header("📅 Historical Analysis")

# Get unique dates sorted in reverse chronological order
available_dates = sorted(changes_df['Date'].unique(), reverse=True)
date_options = [date.strftime('%Y-%m-%d') for date in available_dates]

selected_date_str = st.selectbox(
    "Select announcement date:",
    options=date_options,
    index=0,
    help="Choose a date to view S&P 500 additions and removals"
)

# Convert selected date back to datetime
selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()

# Filter data for selected date
date_data = changes_df[changes_df['Date'] == selected_date]

if date_data.empty:
    st.warning(f"No S&P 500 changes found for {selected_date_str}")
else:
    # Display additions and removals
    col1, col2 = st.columns(2)
    
    additions = date_data[date_data['Change_Type'] == 'Added']
    removals = date_data[date_data['Change_Type'] == 'Removed']
    
    with col1:
        st.subheader("✅ Additions")
        if not additions.empty:
            additions_display = additions[['Symbol', 'Company', 'GICS_Sector']].copy()
            st.dataframe(additions_display, width='stretch', hide_index=True)
        else:
            st.info("No additions on this date")
    
    with col2:
        st.subheader("❌ Removals")
        if not removals.empty:
            removals_display = removals[['Symbol', 'Company', 'Reason']].copy()
            st.dataframe(removals_display, width='stretch', hide_index=True)
        else:
            st.info("No removals on this date")
   
     # Performance analysis section
    st.header("📈 Performance Analysis")
    st.markdown("Stock performance 3 months before and after the announcement date")
    
    # Get all symbols for analysis
    all_symbols = list(additions['Symbol']) + list(removals['Symbol']) if not additions.empty or not removals.empty else []
    
    if all_symbols:
        with st.spinner("Analyzing stock performance..."):
            analyzer = StockAnalyzer()
            
            try:
                # Calculate date ranges
                start_date = selected_date - timedelta(days=90)
                end_date = selected_date + timedelta(days=90)
                
                performance_data = analyzer.get_performance_data(
                    symbols=all_symbols,
                    announcement_date=selected_date,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if not performance_data.empty:
                    # Create performance chart
                    fig = go.Figure()
                    
                    # Add traces for additions
                    if not additions.empty:
                        for symbol in additions['Symbol']:
                            symbol_data = performance_data[performance_data['Symbol'] == symbol]
                            if not symbol_data.empty:
                                fig.add_trace(go.Scatter(
                                    x=symbol_data['Days_From_Announcement'],
                                    y=symbol_data['Rebased_Price'],
                                    mode='lines',
                                    name=f"{symbol} (Added)",
                                    line=dict(color='green', width=2),
                                    hovertemplate=f"<b>{symbol}</b><br>" +
                                                "Days from announcement: %{x}<br>" +
                                                "Rebased price: %{y:.2f}<br>" +
                                                "<extra></extra>"
                                ))
                    
                    # Add traces for removals
                    if not removals.empty:
                        for symbol in removals['Symbol']:
                            symbol_data = performance_data[performance_data['Symbol'] == symbol]
                            if not symbol_data.empty:
                                fig.add_trace(go.Scatter(
                                    x=symbol_data['Days_From_Announcement'],
                                    y=symbol_data['Rebased_Price'],
                                    mode='lines',
                                    name=f"{symbol} (Removed)",
                                    line=dict(color='red', width=2),
                                    hovertemplate=f"<b>{symbol}</b><br>" +
                                                "Days from announcement: %{x}<br>" +
                                                "Rebased price: %{y:.2f}<br>" +
                                                "<extra></extra>"
                                ))
                    
                    # Add vertical line at announcement date
                    fig.add_vline(
                        x=0,
                        line_dash="dash",
                        line_color="black",
                        annotation_text="Announcement Date",
                        annotation_position="top"
                    )
                    
                    # Update layout
                    fig.update_layout(
                        title=f"Stock Performance Around S&P 500 Changes ({selected_date_str})",
                        xaxis_title="Days from Announcement",
                        yaxis_title="Rebased Price (Announcement Date = 1.0)",
                        hovermode='x unified',
                        height=600,
                        showlegend=True,
                        legend=dict(
                            yanchor="top",
                            y=0.99,
                            xanchor="left",
                            x=0.01
                        )
                    )
                    
                    # Add horizontal line at 1.0 (announcement date baseline)
                    fig.add_hline(
                        y=1.0,
                        line_dash="dot",
                        line_color="gray",
                        opacity=0.5
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Summary statistics
                    st.subheader("📊 Performance Summary")
                    
                    # Calculate performance metrics
                    summary_data = []
                    for symbol in all_symbols:
                        symbol_data = performance_data[performance_data['Symbol'] == symbol]
                        if not symbol_data.empty:
                            before_data = symbol_data[symbol_data['Days_From_Announcement'] <= 0]
                            after_data = symbol_data[symbol_data['Days_From_Announcement'] >= 0]
                            
                            if not before_data.empty and not after_data.empty:
                                start_price = before_data.iloc[0]['Rebased_Price']
                                announcement_price = 1.0  # Rebased to 1.0
                                end_price = after_data.iloc[-1]['Rebased_Price']
                                
                                pre_performance = ((announcement_price - start_price) / start_price) * 100
                                post_performance = ((end_price - announcement_price) / announcement_price) * 100
                                
                                change_type = "Added" if symbol in additions['Symbol'].values else "Removed"
                                
                                summary_data.append({
                                    'Symbol': symbol,
                                    'Change_Type': change_type,
                                    'Pre_Announcement_Return_%': round(pre_performance, 2),
                                    'Post_Announcement_Return_%': round(post_performance, 2),
                                    'Total_Return_%': round(pre_performance + post_performance, 2)
                                })
                    
                    if summary_data:
                        summary_df = pd.DataFrame(summary_data)
                        st.dataframe(summary_df, width='stretch', hide_index=True)
                        
                        # Average performance by change type
                        if len(summary_df) > 1:
                            avg_performance = summary_df.groupby('Change_Type').agg({
                                'Pre_Announcement_Return_%': 'mean',
                                'Post_Announcement_Return_%': 'mean',
                                'Total_Return_%': 'mean'
                            }).round(2)
                            
                            st.subheader("📈 Average Performance by Change Type")
                            st.dataframe(avg_performance, width='stretch')
                
                else:
                    st.warning("Unable to retrieve performance data for the selected stocks.")
                    
            except Exception as e:
                st.error(f"Error analyzing performance: {str(e)}")
    else:
        st.info("No stocks to analyze for the selected date.")

# Future Additions Section
st.header("🔮 Future Additions Analysis")
st.markdown("Russell 1000 companies (excluding current S&P 500) most likely to be promoted to the S&P 500")

# Load and analyze Russell 1000 data
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_russell_analysis():
    """Load Russell 1000 companies, filter out S&P 500, and analyze for S&P 500 inclusion likelihood"""
    try:
        analyzer = Russell1000Analyzer()
        # Get S&P 500 candidates from Russell 1000 (filtered automatically)
        candidates = analyzer.get_sp500_candidates(max_companies=30)
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
    top_candidates = candidates_df# .head(400)
    
    # Column mapping for user-friendly names
    column_mapping = {
        'Symbol': 'Symbol',
        'Company': 'Company', 
        'Sector': 'GICS_Sector',
        'Market Cap ($B)': 'Market_Cap_B',
        'Revenue Growth (%)': 'Revenue_Growth_TTM',
        'Profit Margin (%)': 'Profit_Margin',
        'ROE (%)': 'ROE',
        'Score': 'Inclusion_Score'
    }
    
    # Column selector
    available_columns = list(column_mapping.keys())
    selected_columns = st.multiselect(
        "Select columns to display:",
        options=available_columns,
        default=available_columns,
        key="column_selector"
    )
    
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
        
        st.dataframe(display_df, width='stretch', hide_index=True)
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
    **Historical Analysis Data Sources:**
    - S&P 500 historical changes: Wikipedia
    - Stock price data: Yahoo Finance (via yfinance)
    
    **Future Additions Analysis:**
    - Russell 1000 company data: Wikipedia
    - S&P 500 company data: Wikipedia (for filtering)
    - Financial metrics: Yahoo Finance (yfinance)
    - Inclusion scoring: Based on official S&P 500 criteria
    
    **Methodology:**
    - Historical prices are rebased to announcement date (set to 1.0)
    - Analysis covers 3 months before and after the announcement
    - Russell 1000 companies already in S&P 500 are filtered out automatically
    - Inclusion scores consider market cap, profitability, growth, financial health, and liquidity
    - Scores range from 0-100, with 70+ indicating strong inclusion likelihood
    
    **Notes:**
    - Some stocks may not have sufficient historical data
    - Performance analysis excludes weekends and holidays
    - Green lines represent added stocks, red lines represent removed stocks
    - Future inclusion predictions are based on quantitative analysis only
    """)
