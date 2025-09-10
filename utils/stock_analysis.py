import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st

class StockAnalyzer:
    """Analyzer for stock performance around S&P 500 changes"""
    
    def __init__(self):
        pass
    
    def get_performance_data(self, symbols, announcement_date, start_date, end_date):
        """
        Get stock performance data for analysis
        
        Args:
            symbols: List of stock symbols
            announcement_date: Date of S&P 500 change announcement
            start_date: Start date for analysis (typically 3 months before)
            end_date: End date for analysis (typically 3 months after)
        
        Returns:
            DataFrame with columns: Symbol, Date, Price, Rebased_Price, Days_From_Announcement
        """
        all_data = []
        
        for symbol in symbols:
            try:
                # Download stock data
                stock_data = self._download_stock_data(symbol, start_date, end_date)
                
                if stock_data.empty:
                    st.warning(f"No data available for {symbol}")
                    continue
                
                # Rebase prices to announcement date
                rebased_data = self._rebase_prices(stock_data, announcement_date)
                
                if rebased_data.empty:
                    st.warning(f"Unable to rebase prices for {symbol}")
                    continue
                
                # Add symbol column
                rebased_data['Symbol'] = symbol
                
                all_data.append(rebased_data)
                
            except Exception as e:
                st.warning(f"Error processing {symbol}: {str(e)}")
                continue
        
        if all_data:
            result = pd.concat(all_data, ignore_index=True)
            return result
        else:
            return pd.DataFrame()
    
    def _download_stock_data(self, symbol, start_date, end_date):
        """Download stock data from Yahoo Finance"""
        try:
            # Add buffer days to ensure we get data around the target dates
            buffer_start = start_date - timedelta(days=10)
            buffer_end = end_date + timedelta(days=10)
            
            # Download data
            ticker = yf.Ticker(symbol)
            data = ticker.history(
                start=buffer_start,
                end=buffer_end,
                auto_adjust=True,  # Adjust for splits and dividends
                back_adjust=True,
                actions=False  # Don't include dividends and splits columns
            )
            
            if data.empty:
                print(f"No data returned for {symbol}")
                return pd.DataFrame()
            
            # Use adjusted close price
            price_data = data[['Close']].copy()
            price_data.columns = ['Price']
            
            # Reset index to make Date a column
            price_data = price_data.reset_index()
            
            # Ensure Date column is datetime
            if not pd.api.types.is_datetime64_any_dtype(price_data['Date']):
                price_data['Date'] = pd.to_datetime(price_data['Date'])
            
            # Filter to the requested date range
            price_data = price_data[
                (price_data['Date'].dt.date >= start_date) & 
                (price_data['Date'].dt.date <= end_date)
            ]
            
            print(f"Downloaded {len(price_data)} data points for {symbol}")
            return price_data
            
        except Exception as e:
            print(f"Error downloading data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def _rebase_prices(self, stock_data, announcement_date):
        """Rebase stock prices to announcement date (set to 1.0)"""
        if stock_data.empty:
            return pd.DataFrame()
        
        try:
            # Find the closest trading day to announcement date
            stock_data['Date_Only'] = stock_data['Date'].dt.date
            
            # Find announcement date price
            announcement_data = stock_data[stock_data['Date_Only'] == announcement_date]
            
            if announcement_data.empty:
                # Find the closest date (within 5 days)
                stock_data['Days_Diff'] = abs((stock_data['Date_Only'] - announcement_date).apply(lambda x: x.days))
                min_diff_idx = stock_data['Days_Diff'].idxmin()
                min_diff = stock_data.loc[min_diff_idx, 'Days_Diff']
                
                if min_diff > 5:  # If no data within 5 days, skip
                    print(f"No stock data within 5 days of announcement date {announcement_date}")
                    return pd.DataFrame()
                
                announcement_price = stock_data.loc[min_diff_idx, 'Price']
                actual_announcement_date = stock_data.loc[min_diff_idx, 'Date_Only']
                print(f"Using closest date {actual_announcement_date} (diff: {min_diff} days)")
            else:
                announcement_price = announcement_data.iloc[0]['Price']
                actual_announcement_date = announcement_date
                print(f"Found exact announcement date {announcement_date}")
            
            if announcement_price <= 0:
                print(f"Invalid announcement price: {announcement_price}")
                return pd.DataFrame()
            
            # Calculate rebased prices
            stock_data['Rebased_Price'] = stock_data['Price'] / announcement_price
            
            # Calculate days from announcement
            stock_data['Days_From_Announcement'] = (
                stock_data['Date_Only'] - actual_announcement_date
            ).apply(lambda x: x.days)
            
            # Clean up temporary columns
            result = stock_data[['Date', 'Price', 'Rebased_Price', 'Days_From_Announcement']].copy()
            
            # Sort by date
            result = result.sort_values('Date')
            
            print(f"Successfully rebased data: {len(result)} points")
            return result
            
        except Exception as e:
            print(f"Error in rebasing: {str(e)}")
            return pd.DataFrame()
    
    def calculate_performance_metrics(self, performance_data, symbols):
        """Calculate performance metrics for the analysis period"""
        metrics = []
        
        for symbol in symbols:
            symbol_data = performance_data[performance_data['Symbol'] == symbol]
            
            if symbol_data.empty:
                continue
            
            try:
                # Get data before and after announcement
                before_announcement = symbol_data[symbol_data['Days_From_Announcement'] < 0]
                after_announcement = symbol_data[symbol_data['Days_From_Announcement'] > 0]
                announcement_day = symbol_data[symbol_data['Days_From_Announcement'] == 0]
                
                if before_announcement.empty or after_announcement.empty:
                    continue
                
                # Calculate returns
                start_price = before_announcement.iloc[0]['Rebased_Price']
                end_price = after_announcement.iloc[-1]['Rebased_Price']
                announcement_price = 1.0  # Rebased to 1.0
                
                # Pre-announcement return (start to announcement)
                pre_return = ((announcement_price - start_price) / start_price) * 100
                
                # Post-announcement return (announcement to end)
                post_return = ((end_price - announcement_price) / announcement_price) * 100
                
                # Total return
                total_return = ((end_price - start_price) / start_price) * 100
                
                # Volatility (standard deviation of daily returns)
                daily_returns = symbol_data['Rebased_Price'].pct_change().dropna()
                volatility = daily_returns.std() * np.sqrt(252) * 100  # Annualized
                
                metrics.append({
                    'Symbol': symbol,
                    'Pre_Announcement_Return_%': round(pre_return, 2),
                    'Post_Announcement_Return_%': round(post_return, 2),
                    'Total_Return_%': round(total_return, 2),
                    'Volatility_%': round(volatility, 2)
                })
                
            except Exception as e:
                continue
        
        return pd.DataFrame(metrics)
