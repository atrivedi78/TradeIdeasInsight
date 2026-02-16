# CLAUDE.md

## Project Overview

Trade Ideas is a Streamlit-based financial analysis platform for analyzing stock market events and technical patterns. It provides tools for S&P 500 historical change tracking, golden/death cross detection across global indices, and Russell 1000-to-S&P 500 promotion candidate scoring.

## Tech Stack

- **Language**: Python 3.11+
- **Framework**: Streamlit (multi-page app architecture)
- **Data Processing**: pandas, NumPy
- **Visualization**: Plotly (graph_objects and express)
- **Financial Data**: yfinance (Yahoo Finance API)
- **Web Scraping**: BeautifulSoup4, requests, trafilatura
- **Package Manager**: uv (with `uv.lock`); `requirements.txt` also present for pip compatibility
- **Deployment**: Replit (Nix-based, autoscale target)

## Repository Structure

```
app.py                          # Main Streamlit entry point (landing page)
pages/
  sp500_additions.py            # S&P 500 additions/removals analysis page
  golden_death_cross.py         # Golden/death cross alerts page
utils/
  data_scraper.py               # SP500DataScraper - Wikipedia scraper for S&P 500 changes
  stock_analysis.py             # StockAnalyzer - price rebasing and performance metrics
  cross_analyzer.py             # CrossAnalyzer - 50/200-day MA crossover detection
  index_data.py                 # IndexDataFetcher - multi-index constituent fetcher
  sp400_analyzer.py             # Russell1000Analyzer - S&P 500 candidate scoring
.streamlit/config.toml          # Streamlit server config (headless, port 5000)
pyproject.toml                  # Project metadata and direct dependencies
requirements.txt                # Pinned dependency versions
uv.lock                         # UV lock file
.replit                         # Replit deployment and workflow config
```

## Running the Application

```bash
streamlit run app.py --server.port 5000
```

Or via uv:
```bash
uv run streamlit run app.py --server.port 5000
```

## Installing Dependencies

```bash
uv sync
```

Or with pip:
```bash
pip install -r requirements.txt
```

To add a new dependency:
```bash
uv add <package-name>
```

## Architecture

### Multi-Page Streamlit App

- `app.py` is the landing page and configures `st.set_page_config()` (wide layout, expanded sidebar)
- Pages in `pages/` are automatically discovered by Streamlit's multi-page routing
- Each page also calls `st.set_page_config()` at the top (Streamlit requirement for per-page config)

### Utility Layer (`utils/`)

Each utility file contains a single class with a focused responsibility:

| Class | File | Purpose |
|---|---|---|
| `SP500DataScraper` | `data_scraper.py` | Scrapes Wikipedia for historical S&P 500 additions/removals |
| `StockAnalyzer` | `stock_analysis.py` | Downloads price data via yfinance, rebases to announcement dates |
| `CrossAnalyzer` | `cross_analyzer.py` | Detects golden/death crosses using 50-day and 200-day MAs |
| `IndexDataFetcher` | `index_data.py` | Fetches constituent tickers for S&P 500, Nasdaq 100, Russell 1000, FTSE 100, Eurostoxx |
| `Russell1000Analyzer` | `sp400_analyzer.py` | Scores Russell 1000 companies for S&P 500 inclusion likelihood |

### Data Flow

1. **Scraping**: Wikipedia HTML tables are parsed via BeautifulSoup for index constituents and historical changes
2. **Financial Data**: yfinance fetches stock prices, financial metrics, and company info from Yahoo Finance
3. **Analysis**: Utility classes process raw data (rebasing, MA calculation, scoring)
4. **Caching**: `@st.cache_data(ttl=3600)` decorators cache expensive operations for 1 hour
5. **Display**: Plotly charts and Streamlit dataframes render results interactively

### External Data Sources

- **Wikipedia**: S&P 500 composition, Russell 1000 constituents, Nasdaq 100, FTSE 100, Eurostoxx 50
- **Yahoo Finance** (via yfinance): Stock prices, moving averages, RSI, P/E ratios, market cap, volume

## Code Conventions

### Naming

- **Classes**: PascalCase (`SP500DataScraper`, `CrossAnalyzer`, `Russell1000Analyzer`)
- **Methods**: snake_case (`get_historical_changes`, `_rebase_prices`)
- **Private methods**: Prefixed with underscore (`_parse_changes_table`, `_calculate_rsi`)
- **Variables**: snake_case (`announcement_date`, `lookback_days`)
- **DataFrame columns**: PascalCase with underscores (`Change_Type`, `Rebased_Price`, `Days_From_Announcement`)

### File Organization

- One class per utility file, named to match the class's responsibility
- Pages are self-contained Streamlit scripts that import from `utils/`
- Imports follow: stdlib -> third-party -> local utils

### Error Handling

- Web scraping uses try/except with `st.error()` or `st.warning()` for user-facing messages
- Fallback to sample data when scraping fails (see `_create_sample_structure()` methods)
- HTTP requests use 10-15 second timeouts and User-Agent headers
- Individual stock processing failures are caught and skipped (loop continues)

### Caching

- Use `@st.cache_data(ttl=3600)` for expensive data fetches (scraping, API calls)
- The `_self` parameter pattern is used for caching instance methods (Streamlit requirement)

### Visualization

- Plotly `graph_objects` for detailed, custom charts (performance analysis)
- Plotly `express` for quick scatter/bar plots (candidate scoring)
- Common patterns: `fig.add_vline()` for reference dates, `fig.add_hline()` for thresholds
- Charts use `st.plotly_chart(fig, use_container_width=True)`

## Key Technical Details

### S&P 500 Analysis

- Scrapes the second `wikitable` on the S&P 500 Wikipedia page for historical changes
- Prices are rebased so announcement date = 1.0 for cross-stock comparison
- 90-day windows before/after announcement for performance analysis
- Closest trading day within 5 days is used when announcement falls on non-trading day

### Golden/Death Cross Detection

- Golden cross: 50-day MA crosses above 200-day MA (Signal diff == 2)
- Death cross: 50-day MA crosses below 200-day MA (Signal diff == -2)
- Only crosses within the past 7 days are reported
- RSI calculation uses 14-period standard

### S&P 500 Candidate Scoring

- Filters Russell 1000 minus current S&P 500 members
- Scoring weights: Market Cap (30pts), Float (20pts), Liquidity (10pts), Profitability (10pts), Growth (10pts), Financial Health (10pts)
- `criteria_met` boolean tracks hard requirements (market cap >= $22.7B, float >= 50%, liquidity threshold)

## Testing

No formal test framework is configured. The application is tested manually through the Streamlit UI. When adding tests, pytest would be the conventional choice for a Python project of this type.

## Environment & Secrets

No environment variables or API keys are required. All data sources (Wikipedia, Yahoo Finance) are publicly accessible. No `.env` file is used.

## Common Tasks

### Adding a New Analysis Page

1. Create a new file in `pages/` (e.g., `pages/new_analysis.py`)
2. Add `st.set_page_config()` at the top
3. Create utility class(es) in `utils/` if needed (one class per file)
4. Use `@st.cache_data(ttl=3600)` for any expensive data fetches
5. Streamlit auto-discovers pages from the `pages/` directory

### Adding a New Index to Cross Analyzer

1. Add a scraper method `_get_<index_name>()` to `IndexDataFetcher` in `utils/index_data.py`
2. Register it in the `fetchers` dict inside `get_index_constituents()`
3. Add the index name to the `options` list in `pages/golden_death_cross.py`

### Adding a New Utility Class

1. Create a new file in `utils/` named to match the class responsibility
2. Follow the single-class-per-file pattern
3. Use `st.error()`/`st.warning()` for user-facing error reporting
4. Wrap external API calls in try/except with fallback behavior
