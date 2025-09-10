import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
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
            
            # Find all tables
            tables = soup.find_all('table', class_='wikitable')
            
            # Get sector information from the main S&P 500 table (first table)
            sector_data = self._extract_sector_data(tables[0] if tables else None)
            
            changes_data = []
            
            # Look for the historical changes table (second table)
            if len(tables) >= 2:
                changes_data.extend(self._parse_changes_table(tables[1]))
            
            if not changes_data:
                # Fallback: create some sample data structure for demonstration
                st.warning("Could not parse Wikipedia changes table. This may be due to changes in the page structure.")
                return self._create_sample_structure()
            
            # Convert to DataFrame
            df = pd.DataFrame(changes_data)
            
            # Add sector information
            df = self._add_sector_information(df, sector_data)
            
            # Clean and standardize the data
            df = self._clean_data(df)
            
            return df
            
        except Exception as e:
            st.error(f"Error scraping S&P 500 data: {str(e)}")
            return self._create_sample_structure()
    
    def _parse_changes_table(self, table):
        """Parse the changes table from Wikipedia"""
        changes = []
        rows = table.find_all('tr')[2:]  # Skip header rows (first two rows)
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 4:  # Ensure we have enough columns
                try:
                    # Extract data from cells based on Wikipedia structure
                    date_text = cells[0].get_text().strip()
                    
                    # Parse date
                    date = self._parse_date(date_text)
                    if not date:
                        continue
                    
                    # Get reason (last column)
                    reason_text = cells[-1].get_text().strip() if len(cells) > 4 else ""
                    
                    # Handle added stocks
                    if len(cells) >= 3:
                        added_ticker = cells[1].get_text().strip()
                        added_company = cells[2].get_text().strip() if len(cells) > 2 else ""
                        
                        if added_ticker and added_ticker != "—" and added_ticker != "-":
                            changes.append({
                                'Date': date,
                                'Symbol': added_ticker,
                                'Company': added_company or "Unknown Company",
                                'Change_Type': 'Added',
                                'GICS_Sector': "Unknown",  # We'll get this from the main table later
                                'Reason': reason_text
                            })
                    
                    # Handle removed stocks
                    if len(cells) >= 5:
                        removed_ticker = cells[3].get_text().strip()
                        removed_company = cells[4].get_text().strip()
                        
                        if removed_ticker and removed_ticker != "—" and removed_ticker != "-":
                            changes.append({
                                'Date': date,
                                'Symbol': removed_ticker,
                                'Company': removed_company or "Unknown Company",
                                'Change_Type': 'Removed',
                                'GICS_Sector': "Unknown",  # We'll get this from the main table later
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
        
        # Filter out very recent dates (less than 30 days ago) as they may not have sufficient stock data
        # cutoff_date = datetime.now().date() - timedelta(days=30)
        # df = df[df['Date'] <= cutoff_date]
        
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
                'Date': datetime(2024, 6, 24).date(),
                'Symbol': 'TPG',
                'Company': 'TPG Inc.',
                'Change_Type': 'Added',
                'GICS_Sector': 'Financials',
                'Reason': 'Market cap increase'
            },
            {
                'Date': datetime(2024, 6, 24).date(),
                'Symbol': 'SOLV',
                'Company': 'Solventum Corporation',
                'Change_Type': 'Added',
                'GICS_Sector': 'Health Care',
                'Reason': 'Spin-off from 3M'
            },
            {
                'Date': datetime(2024, 3, 18).date(),
                'Symbol': 'SMCI',
                'Company': 'Super Micro Computer',
                'Change_Type': 'Added',
                'GICS_Sector': 'Information Technology',
                'Reason': 'Market cap increase'
            },
            {
                'Date': datetime(2024, 3, 18).date(),
                'Symbol': 'ZBH',
                'Company': 'Zimmer Biomet Holdings',
                'Change_Type': 'Removed',
                'GICS_Sector': 'Health Care',
                'Reason': 'Market cap decrease'
            },
            {
                'Date': datetime(2023, 12, 18).date(),
                'Symbol': 'KKR',
                'Company': 'KKR & Co Inc',
                'Change_Type': 'Added',
                'GICS_Sector': 'Financials',
                'Reason': 'Market cap increase'
            },
            {
                'Date': datetime(2023, 12, 18).date(),
                'Symbol': 'X',
                'Company': 'United States Steel Corporation',
                'Change_Type': 'Removed',
                'GICS_Sector': 'Materials',
                'Reason': 'Market cap decrease'
            }
        ]
        
        return pd.DataFrame(sample_data)
    
    def _extract_sector_data(self, table):
        """Extract sector information from the main S&P 500 table"""
        sector_data = {}
        
        if not table:
            return sector_data
        
        try:
            rows = table.find_all('tr')[1:]  # Skip header row
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:  # Symbol, Security, GICS Sector
                    symbol = cells[0].get_text().strip()
                    company = cells[1].get_text().strip()
                    sector = cells[2].get_text().strip()
                    
                    # Clean the data
                    symbol = re.sub(r'\[.*?\]', '', symbol).strip()
                    company = re.sub(r'\[.*?\]', '', company).strip()
                    sector = re.sub(r'\[.*?\]', '', sector).strip()
                    
                    if symbol and sector:
                        sector_data[symbol] = {
                            'Company': company,
                            'GICS_Sector': sector
                        }
                        
        except Exception as e:
            pass  # Continue even if sector extraction fails
        
        return sector_data
    
    def _add_sector_information(self, df, sector_data):
        """Add sector information to the changes DataFrame"""
        if df.empty or not sector_data:
            return df
        
        # Update sector and company information
        for idx, row in df.iterrows():
            symbol = row['Symbol']
            if symbol in sector_data:
                df.at[idx, 'GICS_Sector'] = sector_data[symbol]['GICS_Sector']
                # Only update company name if it's currently "Unknown Company"
                if row['Company'] == "Unknown Company":
                    df.at[idx, 'Company'] = sector_data[symbol]['Company']
        
        return df
