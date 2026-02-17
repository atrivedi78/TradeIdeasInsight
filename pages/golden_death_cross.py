import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from utils.index_data import IndexDataFetcher
from utils.cross_analyzer import CrossAnalyzer

st.set_page_config(page_title="Golden & Death Cross Alerts - Trade Ideas", page_icon="⚡", layout="wide")

st.title("⚡ Golden & Death Cross Alerts")
st.markdown("Identify stocks with recent golden cross (bullish) or death cross (bearish) signals")

st.markdown("""
### What are Golden and Death Crosses?
- **Golden Cross**: When the 50-day moving average crosses **above** the 200-day moving average (bullish signal)
- **Death Cross**: When the 50-day moving average crosses **below** the 200-day moving average (bearish signal)

This tool scans index constituents for stocks that have experienced these crossovers in the past week.
""")

st.divider()

st.subheader("Settings")
col1, col2, col3 = st.columns(3)

with col1:

    selected_index = st.selectbox(
        "Select Index",
        options=['S&P 500', 'Nasdaq 100', 'Russell 1000', 'FTSE 100', 'Eurostoxx', 'Test Data'],
        help="Choose the market index to analyze"
    )

with col2:
    
    lookback_days = st.slider(
        "Lookback Period (days)",
        min_value=90,
        max_value=365,
        value=180,
        step=30,
        help="Number of days of historical data to analyze"
    )
    
with col3:

    # Add vertical space to align button with other widgets
    st.markdown("<div style='margin-top: 26px;'></div>", unsafe_allow_html=True)
    analyze_button = st.button("🔍 Analyze", type="primary", use_container_width=True)

if analyze_button:

    st.subheader("Results")

    with st.spinner(f"Fetching {selected_index} constituents..."):
        fetcher = IndexDataFetcher()
        symbols = fetcher.get_index_constituents(selected_index)
    
    if not symbols:
        st.error(f"Could not fetch constituents for {selected_index}. Please try another index.")
    else:
        st.success(f"Found {len(symbols)} stocks in {selected_index}")
        
        with st.spinner("Analyzing stocks for golden and death crosses..."):
            analyzer = CrossAnalyzer()
            results = analyzer.analyze_stocks(symbols, lookback_days=lookback_days, max_symbols=10000)
        
        if results.empty:
            st.warning("No golden or death crosses found in the past week for this index.")
        else:
            st.success(f"Found {len(results)} stocks with recent crosses!")
            
            golden_crosses = results[results['Cross_Type'] == 'Golden Cross']
            death_crosses = results[results['Cross_Type'] == 'Death Cross']
            
            metric_col1, metric_col2 = st.columns(2)
            with metric_col1:
                st.metric("Golden Crosses", len(golden_crosses), delta="Bullish", delta_color="normal")
            with metric_col2:
                st.metric("Death Crosses", len(death_crosses), delta="Bearish", delta_color="inverse")
            
            st.divider()
            
            tab1, tab2, tab3 = st.tabs(["📊 All Crosses", "📈 Golden Crosses", "📉 Death Crosses"])
            
            with tab1:
                st.dataframe(
                    results,
                    column_config={
                        "Symbol": st.column_config.TextColumn("Ticker", width="small"),
                        "Company": st.column_config.TextColumn("Company", width="medium"),
                        "Cross_Type": st.column_config.TextColumn("Signal", width="small"),
                        "Cross_Date": st.column_config.DateColumn("Cross Date", width="small"),
                        "Current_Price": st.column_config.NumberColumn("Price", format="$%.2f", width="small"),
                        "MA50": st.column_config.NumberColumn("MA50", format="$%.2f", width="small"),
                        "MA200": st.column_config.NumberColumn("MA200", format="$%.2f", width="small"),
                        "RSI": st.column_config.NumberColumn("RSI", format="%.1f", width="small"),
                        "Forward_PE": st.column_config.NumberColumn("Fwd P/E", format="%.1f", width="small"),
                        "PE_Ratio": st.column_config.NumberColumn("P/E", format="%.1f", width="small"),
                        "Market_Cap_B": st.column_config.NumberColumn("Mkt Cap ($B)", format="%.1f", width="small")
                    },
                    hide_index=True,
                    height = (len(results) + 1) * 35,
                    use_container_width=True
                )
            
            with tab2:
                if not golden_crosses.empty:
                    st.dataframe(
                        golden_crosses,
                        column_config={
                            "Symbol": st.column_config.TextColumn("Ticker", width="small"),
                            "Company": st.column_config.TextColumn("Company", width="medium"),
                            "Cross_Type": st.column_config.TextColumn("Signal", width="small"),
                            "Cross_Date": st.column_config.DateColumn("Cross Date", width="small"),
                            "Current_Price": st.column_config.NumberColumn("Price", format="$%.2f", width="small"),
                            "MA50": st.column_config.NumberColumn("MA50", format="$%.2f", width="small"),
                            "MA200": st.column_config.NumberColumn("MA200", format="$%.2f", width="small"),
                            "RSI": st.column_config.NumberColumn("RSI", format="%.1f", width="small"),
                            "Forward_PE": st.column_config.NumberColumn("Fwd P/E", format="%.1f", width="small"),
                            "PE_Ratio": st.column_config.NumberColumn("P/E", format="%.1f", width="small"),
                            "Market_Cap_B": st.column_config.NumberColumn("Mkt Cap ($B)", format="%.1f", width="small")
                        },
                        hide_index=True,
                        height = (len(results) + 1) * 35,
                        use_container_width=True
                    )
                else:
                    st.info("No golden crosses found in the past week.")
            
            with tab3:
                if not death_crosses.empty:
                    st.dataframe(
                        death_crosses,
                        column_config={
                            "Symbol": st.column_config.TextColumn("Ticker", width="small"),
                            "Company": st.column_config.TextColumn("Company", width="medium"),
                            "Cross_Type": st.column_config.TextColumn("Signal", width="small"),
                            "Cross_Date": st.column_config.DateColumn("Cross Date", width="small"),
                            "Current_Price": st.column_config.NumberColumn("Price", format="$%.2f", width="small"),
                            "MA50": st.column_config.NumberColumn("MA50", format="$%.2f", width="small"),
                            "MA200": st.column_config.NumberColumn("MA200", format="$%.2f", width="small"),
                            "RSI": st.column_config.NumberColumn("RSI", format="%.1f", width="small"),
                            "Forward_PE": st.column_config.NumberColumn("Fwd P/E", format="%.1f", width="small"),
                            "PE_Ratio": st.column_config.NumberColumn("P/E", format="%.1f", width="small"),
                            "Market_Cap_B": st.column_config.NumberColumn("Mkt Cap ($B)", format="%.1f", width="small")
                        },
                        hide_index=True,
                        height = (len(results) + 1) * 35,
                        use_container_width=True
                    )
                else:
                    st.info("No death crosses found in the past week.")
            
            st.divider()
            
            st.download_button(
                label="📥 Download Results (CSV)",
                data=results.to_csv(index=False),
                file_name=f"{selected_index.replace(' ', '_')}_crosses_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )