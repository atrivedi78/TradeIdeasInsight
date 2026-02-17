import requests
from bs4 import BeautifulSoup
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
import re

class Russell1000Analyzer:
    """Analyzer for Russell 1000 companies and their likelihood of S&P 500 inclusion"""
    
    def __init__(self):
        self.russell_url = "https://en.wikipedia.org/wiki/Russell_1000_Index"
        self.sp500_url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # S&P 500 inclusion criteria (current as of 2024/2025)
        self.sp500_criteria = {
            'min_market_cap': 22.7e9,  # $22.7 billion
            'min_float_percentage': 50,  # 50% of shares publicly traded
            'min_monthly_volume': 250000,  # shares per month for 6 months
            'min_liquidity_ratio': 0.75,  # annual volume / float-adjusted market cap
            'profitability_quarters': 4  # positive earnings for trailing 4 quarters
        }
    
    def get_sp500_companies(self):
        """
        Get current S&P 500 companies from Wikipedia
        Returns set of symbols
        """
        try:
            response = requests.get(self.sp500_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the main table with S&P 500 company data
            table = soup.find('table', class_='wikitable')
            
            if not table:
                st.error("Could not find S&P 500 companies table")
                return set()
            
            sp500_symbols = set()
            rows = table.find_all('tr')[1:]  # Skip header row
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 1:
                    try:
                        symbol = cells[0].get_text().strip()
                        # Clean the symbol
                        symbol = re.sub(r'[^\w.-]', '', symbol)
                        
                        if symbol:
                            sp500_symbols.add(symbol)
                            
                    except Exception as e:
                        continue  # Skip problematic rows
            
            print(f"Found {len(sp500_symbols)} S&P 500 companies")
            return sp500_symbols
            
        except Exception as e:
            st.error(f"Error scraping S&P 500 data: {str(e)}")
            return set()
    
    def get_russell1000_companies(self):
        """
        Scrape Russell 1000 companies from Wikipedia
        Returns DataFrame with company information
        """
        try:
            response = requests.get(self.russell_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the components table - look for the table with Company/Symbol headers
            tables = soup.find_all('table', class_='wikitable')
            
            table = None
            for tbl in tables:
                headers = tbl.find('tr')
                if headers:
                    header_text = headers.get_text().lower()
                    if 'company' in header_text and 'symbol' in header_text:
                        table = tbl
                        break
            
            if not table:
                st.error("Could not find Russell 1000 components table with Company/Symbol headers")
                return pd.DataFrame()
            
            companies = []
            rows = table.find_all('tr')[1:]  # Skip header row
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:
                    try:
                        company_name = cells[0].get_text().strip()
                        symbol = cells[1].get_text().strip()
                        gics_sector = cells[2].get_text().strip()
                        gics_sub_industry = cells[3].get_text().strip() if len(cells) > 3 else ""
                        
                        # Clean the data
                        symbol = re.sub(r'[^\w.-]', '', symbol)
                        company_name = re.sub(r'\[.*?\]', '', company_name).strip()
                        
                        if symbol and company_name:
                            companies.append({
                                'Symbol': symbol,
                                'Company': company_name,
                                'GICS_Sector': gics_sector,
                                'GICS_Sub_Industry': gics_sub_industry
                            })
                            
                    except Exception as e:
                        continue  # Skip problematic rows
            
            df = pd.DataFrame(companies)
            print(f"Successfully scraped {len(df)} Russell 1000 companies")
            return df
            
        except Exception as e:
            st.error(f"Error scraping Russell 1000 data: {str(e)}")
            return self._create_sample_russell_data()
    
    def get_sp500_candidates(self, max_companies=30):
        """
        Get Russell 1000 companies, filter out current S&P 500, and analyze for S&P 500 inclusion likelihood
        Returns DataFrame with scores and financial metrics
        """
        # Get Russell 1000 companies
        russell_df = self.get_russell1000_companies()
        if russell_df.empty:
            return pd.DataFrame()
        
        # Get current S&P 500 companies to filter out
        sp500_symbols = self.get_sp500_companies()
        
        # Filter out current S&P 500 companies from Russell 1000
        candidates_df = russell_df[~russell_df['Symbol'].isin(sp500_symbols)]
        
        print(f"Russell 1000: {len(russell_df)} companies, S&P 500: {len(sp500_symbols)} companies")
        print(f"Candidates after filtering: {len(candidates_df)} companies")
        
        if candidates_df.empty:
            return pd.DataFrame()
        
        candidates = []
        
        # Process companies in batches to avoid overwhelming the API
        symbols = candidates_df['Symbol'].tolist()[:max_companies]  # Limit for performance
        
        for symbol in symbols:
            try:
                company_data = candidates_df[candidates_df['Symbol'] == symbol].iloc[0]
                
                # Get financial data
                financial_metrics = self._get_financial_metrics(symbol)
                
                if financial_metrics:
                    # Calculate inclusion score
                    score, criteria_met = self._calculate_inclusion_score(financial_metrics)
                    
                    candidate = {
                        'Symbol': symbol,
                        'Company': company_data['Company'],
                        'GICS_Sector': company_data['GICS_Sector'],
                        'Market_Cap_B': financial_metrics.get('market_cap', 0) / 1e9,
                        'Revenue_Growth_TTM': financial_metrics.get('revenue_growth', 0),
                        'Profit_Margin': financial_metrics.get('profit_margin', 0),
                        'ROE': financial_metrics.get('roe', 0),
                        'Debt_to_Equity': financial_metrics.get('debt_to_equity', 0),
                        'Free_Cash_Flow_B': financial_metrics.get('free_cash_flow', 0) / 1e9,
                        'Average_Volume_M': financial_metrics.get('avg_volume', 0) / 1e6,
                        'Inclusion_Score': score,
                        'criteria_met': criteria_met,
                        'Score_Components': financial_metrics.get('score_breakdown', {})
                    }
                    
                    candidates.append(candidate)
                    
            except Exception as e:
                print(f"Error analyzing {symbol}: {str(e)}")
                continue
        
        # Convert to DataFrame and sort by score
        candidates_df = pd.DataFrame(candidates)
        if not candidates_df.empty:
            candidates_df = candidates_df.sort_values('Inclusion_Score', ascending=False)
        
        return candidates_df
    
    def _get_financial_metrics(self, symbol):
        """Get key financial metrics for a company using yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get historical data for volume analysis
            hist = ticker.history(period="1y")
            
            if info and not hist.empty:
                metrics = {
                    'market_cap': info.get('marketCap', 0),
                    'revenue_growth': info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 0,
                    'profit_margin': info.get('profitMargins', 0) * 100 if info.get('profitMargins') else 0,
                    'roe': info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0,
                    'debt_to_equity': info.get('debtToEquity', 0),
                    'free_cash_flow': info.get('freeCashflow', 0),
                    'avg_volume': hist['Volume'].tail(180).mean(),  # 6-month average
                    'pe_ratio': info.get('trailingPE', 0),
                    'forward_pe': info.get('forwardPE', 0),
                    'price_to_book': info.get('priceToBook', 0),
                    'enterprise_value': info.get('enterpriseValue', 0),
                    'earnings_growth': info.get('earningsGrowth', 0) * 100 if info.get('earningsGrowth') else 0,
                    'shares_outstanding': info.get('sharesOutstanding', 0),
                    'float_shares': info.get('floatShares', 0),
                    'country': info.get('country', ''),
                }
                
                return metrics
            
            return None
            
        except Exception as e:
            print(f"Error getting metrics for {symbol}: {str(e)}")
            return None
    
    def _calculate_inclusion_score(self, metrics):
        """
        Calculate inclusion likelihood score based on S&P 500 criteria

        Current Requirements (2025):

        1 - Market Cap: Minimum $22.7 billion
        2 - Profitability: Positive GAAP earnings (recent quarter + trailing 4 quarters)
        3 - Float: At least 50% of shares publicly traded
        4 - Liquidity: 250,000 shares/month for 6 months + liquidity ratio ≥ 0.75
        5 - Location: US-based company on major US exchange
        6 - Committee Approval: Final discretionary review by S&P Index Committee
        
        Returns score from 0-100 + candidate field showing if inclusion limits have been breached completely
        """
        score = 0
        score_breakdown = {}
        criteria_met = True

        # US Domicile Check (hard requirement)
        country = metrics.get('country', '')
        if country != 'United States':
            criteria_met = False

        # Market Cap Score (30 points max)
        market_cap = metrics.get('market_cap', 0)
        if market_cap >= self.sp500_criteria['min_market_cap']:
            cap_score = min(30, 20 + (market_cap - self.sp500_criteria['min_market_cap']) / 1e9)
            score += cap_score
            score_breakdown['market_cap'] = cap_score
        else:
            # No credit for companies below threshold
            cap_score = 0
            score += cap_score
            score_breakdown['market_cap'] = cap_score
            criteria_met = False

        # Liquidity Score (10 points max)
        avg_volume = metrics.get('avg_volume', 0)
        # Calculate monthly volume: daily average * ~21 trading days
        monthly_volume = avg_volume * 20
        min_monthly_volume = self.sp500_criteria['min_monthly_volume']
        
        if monthly_volume >= min_monthly_volume:
            liquidity_score = 10
        else:
            liquidity_score = max(0, (monthly_volume / min_monthly_volume) * 10)
            criteria_met = False

        score += liquidity_score
        score_breakdown['liquidity'] = liquidity_score

        # Float Score (20 points max)
        market_cap = metrics.get('market_cap',0)
        shares_outstanding = metrics.get('shares_outstanding',0)
        float_shares = metrics.get('float_shares',0)
        
        public_float_pct = ((float_shares / shares_outstanding) * 100) if shares_outstanding > 0 else 0
        
        if public_float_pct >= self.sp500_criteria['min_float_percentage']:
            float_score = 20
        else:
            float_score = 0
            criteria_met = False
        
        score += float_score
        score_breakdown['float'] = float_score
        
        # Profitability Score (10 points max) - not stated criteria
        profit_margin = metrics.get('profit_margin', 0)
        roe = metrics.get('roe', 0)
        if profit_margin > 0 and roe > 0:
            profitability_score = min(10, (profit_margin + roe) / 2)
            score += profitability_score
            score_breakdown['profitability'] = profitability_score
        
        # Growth Score (10 points max) - not stated criteria
        revenue_growth = metrics.get('revenue_growth', 0)
        earnings_growth = metrics.get('earnings_growth', 0)
        if revenue_growth > 0 or earnings_growth > 0:
            growth_score = min(10, max(revenue_growth, earnings_growth) / 2)
            score += growth_score
            score_breakdown['growth'] = growth_score
        
        # Financial Health Score (10 points max) - not stated criteria
        debt_to_equity = metrics.get('debt_to_equity', 100)
        free_cash_flow = metrics.get('free_cash_flow', 0)
        
        # Lower debt is better
        debt_score = max(0, 5 - debt_to_equity / 10) if debt_to_equity > 0 else 5
        
        # Positive free cash flow is good
        fcf_score = 5 if free_cash_flow > 0 else 0
        
        health_score = debt_score + fcf_score
        score += health_score
        score_breakdown['financial_health'] = health_score
        
        metrics['score_breakdown'] = score_breakdown
        return min(100, score), criteria_met
    
    def _create_sample_russell_data(self):
        """Create sample Russell 1000 data structure for demonstration"""
        sample_data = [
            {
                'Symbol': 'SMCI',
                'Company': 'Super Micro Computer Inc',
                'GICS_Sector': 'Information Technology',
                'GICS_Sub_Industry': 'Technology Hardware, Storage & Peripherals',
                'Headquarters': 'San Jose, California'
            },
            {
                'Symbol': 'VICI',
                'Company': 'VICI Properties Inc',
                'GICS_Sector': 'Real Estate',
                'GICS_Sub_Industry': 'Specialized REITs',
                'Headquarters': 'New York, New York'
            },
            {
                'Symbol': 'TPG',
                'Company': 'TPG Inc',
                'GICS_Sector': 'Financials',
                'GICS_Sub_Industry': 'Asset Management & Custody Banks',
                'Headquarters': 'Fort Worth, Texas'
            }
        ]
        
        return pd.DataFrame(sample_data)