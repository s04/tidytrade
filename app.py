import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import time
import polars as pl
from utils.data_fetcher import DataFetcher
from utils.indicators import SessionVolumeProfile
from utils.llm_analyzer import LLMAnalyzer

st.set_page_config(
    page_title="DAX Price Indicator Reviewer",
    page_icon="📈",
    layout="wide"
)

@st.cache_data(ttl=3600)
def load_data(period, interval):
    fetcher = DataFetcher()
    return fetcher.fetch_dax_data(period=period, interval=interval)

@st.cache_data(ttl=3600)
def calculate_volume_profile(df, session_type):
    svp = SessionVolumeProfile(price_bins=30)
    daily_profiles = svp.calculate_daily_profiles(df)
    return daily_profiles

def create_candlestick_chart(df, daily_profiles):
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("DAX Candlestick Chart with Daily Session Volume Profiles", "Volume Timeline"),
        specs=[[{"secondary_y": False}], [{"secondary_y": False}]],
        vertical_spacing=0.1,
        row_heights=[0.75, 0.25]
    )
    
    candlestick = go.Candlestick(
        x=df['datetime'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name="DAX",
        showlegend=False
    )
    fig.add_trace(candlestick, row=1, col=1)
    
    # Add daily volume profiles
    df_with_date = df.with_columns(pl.col('datetime').dt.date().alias('date'))
    
    for date_str, profile_data in daily_profiles.items():
        # Get the day's data to position the profile
        daily_data = df_with_date.filter(pl.col('date').cast(str) == date_str)
        if len(daily_data) == 0:
            continue
            
        day_start = daily_data['datetime'].min()
        day_end = daily_data['datetime'].max()
        
        # Calculate profile width (20% of the day's time span to the left)
        time_span = day_end - day_start
        profile_width = time_span * 0.2
        profile_start = day_start - profile_width
        
        max_volume = max(profile_data['volume_profile']) if max(profile_data['volume_profile']) > 0 else 1
        
        # Draw horizontal lines for each price level
        for price, volume in zip(profile_data['price_levels'], profile_data['volume_profile']):
            if volume > max_volume * 0.1:  # Only show significant volume (>10% of max)
                line_length = (volume / max_volume) * profile_width
                fig.add_shape(
                    type="line",
                    x0=profile_start, x1=profile_start + line_length,
                    y0=price, y1=price,
                    line=dict(color="rgba(255, 165, 0, 0.7)", width=2),
                    row=1, col=1
                )
        
        # Add POC line for this day
        fig.add_shape(
            type="line",
            x0=profile_start, x1=profile_start + profile_width,
            y0=profile_data['poc'], y1=profile_data['poc'],
            line=dict(color="red", width=3, dash="dot"),
            row=1, col=1
        )
    
    volume_chart = go.Bar(
        x=df['datetime'],
        y=df['volume'],
        name="Volume Timeline",
        marker_color="rgba(70,130,180,0.7)",
        showlegend=False
    )
    fig.add_trace(volume_chart, row=2, col=1)
    
    fig.update_layout(
        title="DAX Analysis Dashboard",
        height=800,
        xaxis_rangeslider_visible=False
    )
    
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_yaxes(title_text="Price (€)", row=1, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    
    return fig

def main():
    st.title("📈 DAX Price Indicator Reviewer")
    st.markdown("Real-time DAX analysis with Session Volume Profile and AI insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        period = st.selectbox(
            "Timeframe",
            ["1d", "5d", "1mo"],
            index=1
        )
    
    with col2:
        interval = st.selectbox(
            "Granularity",
            ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d"],
            index=7
        )
    
    with col3:
        session_type = st.selectbox(
            "Session Type",
            ["Full Day", "European Session", "US Session"],
            index=0
        )
    
    if st.button("🔄 Refresh Data", type="primary"):
        st.cache_data.clear()
    
    try:
        with st.spinner("Loading DAX data..."):
            df = load_data(period, interval)
        
        if df.is_empty():
            st.error("No data available for the selected parameters")
            return
    except Exception as e:
        st.error(f"Failed to load DAX data: {str(e)}")
        st.info("Please try again or contact support if the issue persists.")
        return
    
    with st.spinner("Calculating volume profile..."):
        daily_profiles = calculate_volume_profile(df, session_type)
    
    fig = create_candlestick_chart(df, daily_profiles)
    st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📊 Market Data")
        latest = df.tail(1).to_dicts()[0]
        
        st.metric(
            "Current Price", 
            f"{latest['close']:.2f}",
            f"{latest['close'] - latest['open']:+.2f}"
        )
        
        # Show latest day's POC
        if daily_profiles:
            latest_date = max(daily_profiles.keys())
            latest_poc = daily_profiles[latest_date]['poc']
            latest_volume = daily_profiles[latest_date]['total_volume']
            st.metric("Latest POC", f"{latest_poc:.2f}")
            st.metric("Latest Day Volume", f"{latest_volume:,.0f}")
        
        st.subheader("📈 Price Levels")
        st.write(f"**High:** {latest['high']:.2f}")
        st.write(f"**Low:** {latest['low']:.2f}")
        st.write(f"**Open:** {latest['open']:.2f}")
        st.write(f"**Close:** {latest['close']:.2f}")
    
    with col2:
        st.subheader("🤖 AI Analysis")
        
        # Expandable prompt editor
        with st.expander("📝 Customize Analysis Prompt", expanded=False):
            custom_prompt = st.text_area(
                "AI Analysis Prompt:",
                value="""Analyze this DAX price action data and provide a concise trading report:

{summary}

Please provide:
1. Market Sentiment (Bullish/Bearish/Neutral)
2. Key Support/Resistance Levels
3. Volume Analysis Insights
4. Potential Trading Opportunities
5. Risk Considerations

Keep the analysis practical and actionable for traders.""",
                height=200,
                help="Customize how the AI analyzes your DAX data. Use {summary} placeholder for data insertion."
            )
        
        if st.button("Generate AI Report", type="secondary"):
            with st.spinner("Generating AI analysis..."):
                try:
                    if daily_profiles:
                        # Use the latest day's profile for AI analysis
                        latest_date = max(daily_profiles.keys())
                        latest_profile = daily_profiles[latest_date]
                        analyzer = LLMAnalyzer()
                        analysis = analyzer.analyze_price_action(df, latest_profile, custom_prompt)
                        st.markdown(analysis)
                    else:
                        st.error("No volume profile data available for analysis")
                except Exception as e:
                    st.error(f"AI analysis failed: {str(e)}")
                    st.info("Make sure to set your ANTHROPIC_API_KEY in .streamlit/secrets.toml")
    
    # Footer
    st.markdown("---")
    st.markdown("*DAX Price Indicator Reviewer - Built with Streamlit, Polars, and Claude AI*")

if __name__ == "__main__":
    main()