import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
from typing import Any
from utils.data_scraper import SP500DataScraper
from utils.stock_analysis import StockAnalyzer
from utils.sp400_analyzer import SP400Analyzer

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

# Additional information
with st.expander("ℹ️ About this Analysis"):
    st.markdown("""
    **Data Sources:**
    - S&P 500 historical changes: Wikipedia
    - Stock price data: Yahoo Finance (via yfinance)
    
    **Methodology:**
    - Prices are rebased to the announcement date (set to 1.0)
    - Analysis covers 3 months before and after the announcement
    - All prices are adjusted for splits and dividends
    
    **Notes:**
    - Some stocks may not have sufficient historical data
    - Performance analysis excludes weekends and holidays
    - Green lines represent added stocks, red lines represent removed stocks
    """)
