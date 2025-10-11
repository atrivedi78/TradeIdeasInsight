import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import re

class IndexDataFetcher:
    """Fetch constituent tickers for various global indices"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    @st.cache_data(ttl=3600)
    def get_index_constituents(_self, index_name):
        """Get constituents for the selected index"""
        fetchers = {
            'S&P 500': _self._get_sp500,
            'Nasdaq 100': _self._get_nasdaq100,
            'Russell 1000': _self._get_russell1000,
            'FTSE 100': _self._get_ftse100,
            'Eurostoxx': _self._get_eurostoxx
        }
        
        if index_name in fetchers:
            return fetchers[index_name]()
        else:
            st.error(f"Unknown index: {index_name}")
            return []
    
    def _get_sp500(self):
        """Get S&P 500 constituents from Wikipedia"""
        try:
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', class_='wikitable')
            
            if not table:
                st.error("Could not find S&P 500 table")
                return []
            
            symbols = []
            rows = table.find_all('tr')[1:]
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 1:
                    try:
                        symbol = cells[0].get_text().strip()
                        symbol = re.sub(r'[^\w.-]', '', symbol)
                        if symbol:
                            symbols.append(symbol)
                    except:
                        continue
            
            return symbols
            
        except Exception as e:
            st.error(f"Error fetching S&P 500 data: {str(e)}")
            return []
    
    def _get_nasdaq100(self):
        """Get Nasdaq 100 constituents from Wikipedia"""
        try:
            url = "https://en.wikipedia.org/wiki/Nasdaq-100"
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', {'id': 'constituents'})
            
            if not table:
                table = soup.find('table', class_='wikitable')
            
            if not table:
                st.error("Could not find Nasdaq 100 table")
                return []
            
            symbols = []
            rows = table.find_all('tr')[1:]
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    try:
                        symbol = cells[1].get_text().strip()
                        symbol = re.sub(r'[^\w.-]', '', symbol)
                        if symbol and symbol not in ['Ticker', 'Symbol']:
                            symbols.append(symbol)
                    except:
                        continue
            
            return symbols
            
        except Exception as e:
            st.error(f"Error fetching Nasdaq 100 data: {str(e)}")
            return []
    
    def _get_russell1000(self):
        """Get Russell 1000 constituents"""
        try:
            url = "https://en.wikipedia.org/wiki/Russell_1000_Index"
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', class_='wikitable')
            
            if table:
                symbols = []
                rows = table.find_all('tr')[1:]
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 1:
                        try:
                            symbol = cells[0].get_text().strip()
                            symbol = re.sub(r'[^\w.-]', '', symbol)
                            if symbol:
                                symbols.append(symbol)
                        except:
                            continue
                
                if symbols:
                    return symbols
            
            st.warning("Russell 1000 data not available from Wikipedia. Using sample data.")
            return []
            
        except Exception as e:
            st.warning(f"Russell 1000 data not available: {str(e)}")
            return []
    
    def _get_ftse100(self):
        """Get FTSE 100 constituents from Wikipedia"""
        try:
            url = "https://en.wikipedia.org/wiki/FTSE_100_Index"
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', {'id': 'constituents'})
            
            if not table:
                table = soup.find('table', class_='wikitable')
            
            if not table:
                st.error("Could not find FTSE 100 table")
                return []
            
            symbols = []
            rows = table.find_all('tr')[1:]
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    try:
                        symbol = cells[1].get_text().strip()
                        if '.L' not in symbol:
                            symbol = symbol + '.L'
                        symbol = re.sub(r'[^\w.-]', '', symbol)
                        if symbol:
                            symbols.append(symbol)
                    except:
                        continue
            
            return symbols
            
        except Exception as e:
            st.error(f"Error fetching FTSE 100 data: {str(e)}")
            return []
    
    def _get_eurostoxx(self):
        """Get Eurostoxx 50 constituents from Wikipedia"""
        try:
            url = "https://en.wikipedia.org/wiki/EURO_STOXX_50"
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', {'id': 'constituents'})
            
            if not table:
                table = soup.find('table', class_='wikitable')
            
            if not table:
                st.error("Could not find Eurostoxx table")
                return []
            
            symbols = []
            rows = table.find_all('tr')[1:]
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    try:
                        symbol = cells[1].get_text().strip()
                        symbol = re.sub(r'[^\w.-]', '', symbol)
                        if symbol:
                            symbols.append(symbol)
                    except:
                        continue
            
            return symbols
            
        except Exception as e:
            st.error(f"Error fetching Eurostoxx data: {str(e)}")
            return []
