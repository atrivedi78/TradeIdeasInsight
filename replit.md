# Trade Ideas - Financial Analysis Platform

## Overview

Trade Ideas is a Streamlit-based financial analysis platform focused on S&P 500 historical changes and stock performance tracking. The application provides comprehensive analysis tools for examining S&P 500 additions and removals, with performance tracking capabilities that analyze stock behavior 3 months before and after announcement dates. The platform scrapes historical data from Wikipedia and integrates with Yahoo Finance for real-time stock data, offering interactive visualizations and date-based filtering for market event analysis.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web application with multi-page architecture
- **Layout**: Wide layout with expandable sidebar navigation
- **Page Structure**: Main landing page (`app.py`) with dedicated analysis pages in `/pages/` directory
- **Visualization**: Plotly integration for interactive charts and graphs
- **Caching**: Streamlit caching decorators for performance optimization (1-hour TTL for data)

### Backend Architecture
- **Data Processing**: Modular utility classes in `/utils/` directory
- **Web Scraping**: BeautifulSoup-based scraper for Wikipedia S&P 500 historical data
- **Stock Analysis**: Yahoo Finance API integration through yfinance library
- **Data Pipeline**: ETL process that scrapes, cleans, and transforms financial data

### Data Processing Components
- **SP500DataScraper**: Handles Wikipedia scraping for historical S&P 500 changes
- **StockAnalyzer**: Manages stock performance analysis and price rebasing calculations
- **Data Transformation**: Price normalization relative to announcement dates for comparative analysis

### Analysis Features
- **Historical Tracking**: S&P 500 additions/removals with date-based filtering
- **Performance Analysis**: 3-month pre/post announcement performance tracking
- **Price Rebasing**: Normalization of stock prices to announcement dates for comparison
- **Interactive Selection**: Date-based filtering with reverse chronological ordering

## External Dependencies

### Data Sources
- **Wikipedia**: Primary source for S&P 500 historical changes data via web scraping
- **Yahoo Finance**: Stock price data and financial metrics through yfinance API

### Python Libraries
- **streamlit**: Web application framework and UI components
- **pandas**: Data manipulation and analysis
- **plotly**: Interactive data visualization (graph_objects and express)
- **yfinance**: Yahoo Finance API client for stock data
- **requests**: HTTP library for web scraping
- **beautifulsoup4**: HTML parsing for Wikipedia data extraction
- **numpy**: Numerical computing support

### Infrastructure Requirements
- **Web Scraping**: HTTP requests to Wikipedia with proper user-agent headers
- **Data Caching**: Streamlit's built-in caching system for performance optimization
- **Error Handling**: Robust exception handling for data source failures and API rate limits