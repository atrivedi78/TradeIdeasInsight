import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st

class CrossAnalyzer:
    """Analyzer for detecting golden and death crosses in stocks"""
    
    def __init__(self):
        self.short_ma = 50
        self.long_ma = 200
    
    def analyze_stocks(self, symbols, lookback_days=180):
        """
        Analyze stocks for golden and death crosses
        
        Args:
            symbols: List of stock symbols to analyze
            lookback_days: Number of days to look back for price data (default 180 = ~6 months)
        
        Returns:
            DataFrame with stocks that have had recent crosses
        """
        results = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days + self.long_ma)
        
        total_symbols = len(symbols)
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, symbol in enumerate(symbols):
            try:
                status_text.text(f"Analyzing {symbol}... ({idx + 1}/{total_symbols})")
                progress_bar.progress((idx + 1) / total_symbols)
                
                cross_data = self._check_cross(symbol, start_date, end_date)
                
                if cross_data:
                    results.append(cross_data)
                    
            except Exception as e:
                continue
        
        progress_bar.empty()
        status_text.empty()
        
        if results:
            df = pd.DataFrame(results)
            df = df.sort_values('Cross_Date', ascending=False)
            return df
        else:
            return pd.DataFrame()
    
    def _check_cross(self, symbol, start_date, end_date):
        """Check if a stock has had a golden or death cross in the past week"""
        try:
            ticker = yf.Ticker(symbol)
            
            hist = ticker.history(start=start_date, end=end_date, auto_adjust=True)
            
            if hist.empty or len(hist) < self.long_ma:
                return None
            
            hist['MA50'] = hist['Close'].rolling(window=self.short_ma).mean()
            hist['MA200'] = hist['Close'].rolling(window=self.long_ma).mean()
            
            hist = hist.dropna()
            
            if len(hist) < 10:
                return None
            
            hist['Signal'] = np.where(hist['MA50'] > hist['MA200'], 1, -1)
            hist['Cross'] = hist['Signal'].diff()
            
            one_week_ago = end_date - timedelta(days=7)
            recent_data = hist[hist.index >= one_week_ago]
            
            if recent_data.empty:
                return None
            
            golden_cross = recent_data[recent_data['Cross'] == 2]
            death_cross = recent_data[recent_data['Cross'] == -2]
            
            cross_type = None
            cross_date = None
            
            if not golden_cross.empty:
                cross_type = 'Golden Cross'
                cross_date = golden_cross.index[-1]
            elif not death_cross.empty:
                cross_type = 'Death Cross'
                cross_date = death_cross.index[-1]
            
            if cross_type:
                latest_data = hist.iloc[-1]
                current_price = latest_data['Close']
                ma50 = latest_data['MA50']
                ma200 = latest_data['MA200']
                
                rsi = self._calculate_rsi(hist['Close'])
                
                info = ticker.info
                forward_pe = info.get('forwardPE', None)
                pe_ratio = info.get('trailingPE', None)
                market_cap = info.get('marketCap', None)
                company_name = info.get('longName', symbol)
                
                return {
                    'Symbol': symbol,
                    'Company': company_name,
                    'Cross_Type': cross_type,
                    'Cross_Date': cross_date.strftime('%Y-%m-%d'),
                    'Current_Price': round(current_price, 2),
                    'MA50': round(ma50, 2),
                    'MA200': round(ma200, 2),
                    'RSI': round(rsi, 2) if rsi else None,
                    'Forward_PE': round(forward_pe, 2) if forward_pe else None,
                    'PE_Ratio': round(pe_ratio, 2) if pe_ratio else None,
                    'Market_Cap_B': round(market_cap / 1e9, 2) if market_cap else None
                }
            
            return None
            
        except Exception as e:
            return None
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator"""
        try:
            delta = prices.diff()
            
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.iloc[-1] if not rsi.empty else None
            
        except Exception as e:
            return None
