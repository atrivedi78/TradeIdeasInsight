import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import streamlit as st

class SP500DataScraper:
    """Scraper for S&P 500 historical changes from Wikipedia"""
    
    def __init__(self):
        self.url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def get_historical_changes(self):
        """
        Scrape S&P 500 historical changes from Wikipedia
        Returns DataFrame with columns: Date, Symbol, Company, Change_Type, GICS_Sector, Reason
        """
        try:
            # Fetch the webpage
            response = requests.get(self.url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the changes table - usually the second table on the page
            tables = soup.find_all('table', class_='wikitable')
            
            changes_data = []
            
            # Look for the historical changes table
            for table in tables:
                # Check if this table contains historical changes
                headers = table.find('tr')
                if headers and hasattr(headers, 'find_all'):
                    header_cells = headers.find_all(['th', 'td'])
                    if any('date' in th.get_text().lower() for th in header_cells if hasattr(th, 'get_text')):
                        changes_data.extend(self._parse_changes_table(table))
            
            if not changes_data:
                # Fallback: create some sample data structure for demonstration
                st.warning("Could not parse Wikipedia changes table. This may be due to changes in the page structure.")
                return self._create_sample_structure()
            
            # Convert to DataFrame
            df = pd.DataFrame(changes_data)
            
            # Clean and standardize the data
            df = self._clean_data(df)
            
            return df
            
        except Exception as e:
            st.error(f"Error scraping S&P 500 data: {str(e)}")
            return self._create_sample_structure()
    
    def _parse_changes_table(self, table):
        """Parse the changes table from Wikipedia"""
        changes = []
        rows = table.find_all('tr')[1:]  # Skip header row
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 4:  # Ensure we have enough columns
                try:
                    # Extract data from cells
                    date_text = cells[0].get_text().strip()
                    added_text = cells[1].get_text().strip() if len(cells) > 1 else ""
                    removed_text = cells[2].get_text().strip() if len(cells) > 2 else ""
                    reason_text = cells[3].get_text().strip() if len(cells) > 3 else ""
                    
                    # Parse date
                    date = self._parse_date(date_text)
                    if not date:
                        continue
                    
                    # Parse additions
                    if added_text and added_text != "—" and added_text != "-":
                        added_info = self._parse_stock_info(added_text)
                        for symbol, company, sector in added_info:
                            changes.append({
                                'Date': date,
                                'Symbol': symbol,
                                'Company': company,
                                'Change_Type': 'Added',
                                'GICS_Sector': sector,
                                'Reason': reason_text
                            })
                    
                    # Parse removals
                    if removed_text and removed_text != "—" and removed_text != "-":
                        removed_info = self._parse_stock_info(removed_text)
                        for symbol, company, sector in removed_info:
                            changes.append({
                                'Date': date,
                                'Symbol': symbol,
                                'Company': company,
                                'Change_Type': 'Removed',
                                'GICS_Sector': sector,
                                'Reason': reason_text
                            })
                            
                except Exception as e:
                    continue  # Skip problematic rows
        
        return changes
    
    def _parse_date(self, date_text):
        """Parse date from various formats"""
        try:
            # Clean the date text
            date_text = re.sub(r'\[.*?\]', '', date_text).strip()
            
            # Try different date formats
            date_formats = [
                '%B %d, %Y',
                '%b %d, %Y', 
                '%Y-%m-%d',
                '%m/%d/%Y',
                '%d %B %Y',
                '%d %b %Y'
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_text, fmt).date()
                except ValueError:
                    continue
            
            # Try to extract year and create a date
            year_match = re.search(r'(\d{4})', date_text)
            if year_match:
                year = int(year_match.group(1))
                # Default to January 1st if we can't parse the full date
                return datetime(year, 1, 1).date()
            
            return None
            
        except Exception:
            return None
    
    def _parse_stock_info(self, stock_text):
        """Parse stock symbol, company name, and sector from text"""
        stocks = []
        
        # Clean the text
        stock_text = re.sub(r'\[.*?\]', '', stock_text)
        
        # Look for patterns like "SYMBOL (Company Name)"
        pattern = r'([A-Z]{1,5})\s*\(([^)]+)\)'
        matches = re.findall(pattern, stock_text)
        
        if matches:
            for symbol, company in matches:
                stocks.append((symbol.strip(), company.strip(), "Unknown"))
        else:
            # Try to extract just symbols
            symbol_pattern = r'\b([A-Z]{1,5})\b'
            symbols = re.findall(symbol_pattern, stock_text)
            for symbol in symbols:
                if len(symbol) >= 1 and symbol.isalpha():
                    stocks.append((symbol, "Unknown Company", "Unknown"))
        
        return stocks
    
    def _clean_data(self, df):
        """Clean and standardize the DataFrame"""
        if df.empty:
            return df
        
        # Remove duplicates
        df = df.drop_duplicates()
        
        # Sort by date (newest first)
        df = df.sort_values('Date', ascending=False)
        
        # Clean company names
        df['Company'] = df['Company'].str.replace(r'\[.*?\]', '', regex=True)
        df['Company'] = df['Company'].str.strip()
        
        # Clean symbols
        df['Symbol'] = df['Symbol'].str.upper().str.strip()
        
        # Filter out invalid symbols
        df = df[df['Symbol'].str.match(r'^[A-Z]{1,5}$')]
        
        # Reset index
        df = df.reset_index(drop=True)
        
        return df
    
    def _create_sample_structure(self):
        """Create sample DataFrame structure for demonstration"""
        sample_data = [
            {
                'Date': datetime(2024, 12, 16).date(),
                'Symbol': 'TPG',
                'Company': 'TPG Inc.',
                'Change_Type': 'Added',
                'GICS_Sector': 'Financials',
                'Reason': 'Market cap increase'
            },
            {
                'Date': datetime(2024, 12, 16).date(),
                'Symbol': 'ZION',
                'Company': 'Zions Bancorporation',
                'Change_Type': 'Removed',
                'GICS_Sector': 'Financials',
                'Reason': 'Market cap decrease'
            },
            {
                'Date': datetime(2024, 9, 23).date(),
                'Symbol': 'SMCI',
                'Company': 'Super Micro Computer',
                'Change_Type': 'Added',
                'GICS_Sector': 'Information Technology',
                'Reason': 'Market cap increase'
            },
            {
                'Date': datetime(2024, 9, 23).date(),
                'Symbol': 'ETSY',
                'Company': 'Etsy Inc.',
                'Change_Type': 'Removed',
                'GICS_Sector': 'Consumer Discretionary',
                'Reason': 'Market cap decrease'
            }
        ]
        
        return pd.DataFrame(sample_data)
