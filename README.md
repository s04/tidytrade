# DAX Price Indicator Reviewer

A Streamlit application for analyzing DAX (German stock index) price action with Session Volume Profile indicators and AI-powered insights using Anthropic Claude.

## Features

- Real-time DAX data fetching via yfinance
- Interactive candlestick charts with Plotly
- Session Volume Profile indicator overlay
- High-performance data processing with Polars
- AI analysis using Anthropic Claude 4 Sonnet
- Data caching for improved performance
- Dockerized deployment ready

## Quick Start

1. **Setup Environment**
   ```bash
   pyinit  # Creates and activates virtual environment with dependencies
   ```

2. **Configure API Key**
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   # Edit .streamlit/secrets.toml and add your ANTHROPIC_API_KEY
   ```

3. **Run Application**
   ```bash
   source .venv/bin/activate
   streamlit run app.py
   ```

4. **Docker Deployment**
   ```bash
   docker build -t dax-reviewer .
   # For deployment, configure secrets via platform environment variables
   docker run -p 8501:8501 -e ANTHROPIC_API_KEY=your_key dax-reviewer
   ```

## Usage

- Select timeframe (1d to 2y) and granularity (1m to 1d)
- Choose session type for volume profile analysis
- View interactive candlestick charts with volume profile overlay  
- Generate AI-powered trading insights and reports

## Architecture

```
├── app.py                 # Main Streamlit application
├── utils/
│   ├── data_fetcher.py    # yfinance + Polars data handling
│   ├── indicators.py      # Session Volume Profile calculations
│   ├── llm_analyzer.py    # Anthropic Claude integration
│   └── cache_manager.py   # Data caching utilities
├── cache/                 # Cached data storage
└── Dockerfile            # Container configuration
```

## Tech Stack

- **Frontend**: Streamlit
- **Data**: yfinance, Polars  
- **Visualization**: Plotly
- **AI**: Anthropic Claude 4 Sonnet
- **Containerization**: Docker