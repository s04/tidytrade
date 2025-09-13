# AI Session Profile Monitor

A Streamlit application for analyzing DAX (German stock index) price action with advanced Session Volume Profile indicators and AI-powered insights using Anthropic Claude.

## Features

- **Real-time DAX data** fetching via yfinance with Polars optimization
- **Interactive candlestick charts** with daily session volume profiles
- **Advanced volume analysis**: POC, Volume Cliffs, Statistical Quartiles
- **AI-powered insights** with customizable prompts using Claude 4 Sonnet
- **Smart caching** for improved performance (1-hour TTL)
- **Mobile-optimized** with device-specific recommendations
- **Dockerized** for easy deployment

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
   docker build -t ai-session-monitor .
   # For deployment, configure secrets via platform environment variables
   docker run -p 8501:8501 -e ANTHROPIC_API_KEY=your_key ai-session-monitor
   ```

## Usage

### Getting Started
- **Desktop**: Select 5d timeframe for optimal performance
- **Mobile**: Use 1d timeframe for best mobile experience
- **Chart Navigation**: Refresh page if chart accidentally moves

### Volume Profile Features
- **Blue bars**: Show volume distribution at each price level
- **Yellow POC line**: Indicates Point of Control (highest volume price)
- **Toggleable labels**: 
  - POC Labels (price & volume at POC)
  - Volume Cliffs (natural breakpoints)
  - Statistical Quartiles (MIN, Q1, Q3, MAX)

### AI Analysis
- **Custom prompts**: Edit analysis instructions in expandable prompt editor
- **Context-aware**: Automatically includes enabled annotation data
- **Comprehensive**: Analyzes price action, volume patterns, and support/resistance levels

## Architecture

```
├── app.py                          # Main Streamlit application
├── .streamlit/
│   ├── secrets.toml.example       # API key template
│   └── secrets.toml               # Your API keys (gitignored)
├── utils/
│   ├── data_fetcher.py            # yfinance + Polars data handling
│   ├── indicators.py              # Session Volume Profile calculations
│   ├── llm_analyzer.py            # Anthropic Claude integration
│   └── cache_manager.py           # Smart caching utilities
├── cache/                         # Cached data storage (parquet files)
├── requirements.txt               # Python dependencies
└── Dockerfile                     # Container configuration
```

## Tech Stack

- **Frontend**: Streamlit (latest)
- **Data Processing**: yfinance, Polars (30x faster than pandas)
- **Visualization**: Plotly with interactive volume profiles
- **AI**: Anthropic Claude 4 Sonnet with custom prompt support
- **Caching**: Polars parquet format for optimal performance
- **Deployment**: Docker with Streamlit secrets management