import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import time
import polars as pl
import numpy as np
from utils.data_fetcher import DataFetcher
from utils.indicators import SessionVolumeProfile
from utils.llm_analyzer import LLMAnalyzer

st.set_page_config(
    page_title="AI Session Profile Monitor",
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

def create_candlestick_chart(df, daily_profiles, show_poc_labels=True, show_quartile_labels=False, show_cliff_labels=False):
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
        
        # Calculate profile width (40% of the day's time span to the left)
        time_span = day_end - day_start
        profile_width = time_span * 0.4
        profile_start = day_start - profile_width * 1.5  # Move further left into gap
        
        max_volume = max(profile_data['volume_profile']) if max(profile_data['volume_profile']) > 0 else 1
        
        # Draw horizontal lines for each price level with poppier styling
        for price, volume in zip(profile_data['price_levels'], profile_data['volume_profile']):
            if volume > max_volume * 0.05:  # Show more volume levels (>5% of max)
                line_length = (volume / max_volume) * profile_width
                fig.add_shape(
                    type="line",
                    x0=profile_start, x1=profile_start + line_length,
                    y0=price, y1=price,
                    line=dict(color="rgba(30, 144, 255, 0.9)", width=4),  # Bright blue
                    row=1, col=1
                )
        
        # Add POC line for this day - more prominent
        fig.add_shape(
            type="line",
            x0=profile_start, x1=profile_start + profile_width,
            y0=profile_data['poc'], y1=profile_data['poc'],
            line=dict(color="rgba(255, 215, 0, 0.95)", width=5, dash="solid"),  # Bright yellow/gold
            row=1, col=1
        )
        
        # Add annotations based on toggle settings
        if show_poc_labels or show_quartile_labels or show_cliff_labels:
            # Calculate volume-weighted price quartiles for boxplot-style analysis
            prices = np.array(profile_data['price_levels'])
            volumes = np.array(profile_data['volume_profile'])
            
            # Find significant volume levels (>5% of max)
            significant_mask = volumes > max_volume * 0.05
            sig_prices = prices[significant_mask]
            sig_volumes = volumes[significant_mask]
            
            if len(sig_prices) > 0:
                poc_volume = max(volumes)
                poc_idx = np.argmax(volumes)
                
                if show_cliff_labels:
                    # Find volume cliffs - natural breakpoints in distribution
                    # Look for significant drops from POC area
                    poc_volume_threshold = poc_volume * 0.6  # 60% of POC volume
                    
                    # Find upper and lower cliffs from POC
                    upper_cliff_price = None
                    lower_cliff_price = None
                    upper_cliff_vol = 0
                    lower_cliff_vol = 0
                    
                    # Search above POC for upper cliff
                    for i in range(poc_idx, len(volumes)):
                        if volumes[i] < poc_volume_threshold and volumes[i] > max_volume * 0.1:
                            upper_cliff_price = prices[i]
                            upper_cliff_vol = volumes[i]
                            break
                    
                    # Search below POC for lower cliff
                    for i in range(poc_idx, -1, -1):
                        if volumes[i] < poc_volume_threshold and volumes[i] > max_volume * 0.1:
                            lower_cliff_price = prices[i]
                            lower_cliff_vol = volumes[i]
                            break
                    
                    # Add cliff annotations
                    cliff_stats = []
                    if upper_cliff_price is not None:
                        cliff_stats.append((upper_cliff_price, upper_cliff_vol, "UPPER"))
                    if lower_cliff_price is not None:
                        cliff_stats.append((lower_cliff_price, lower_cliff_vol, "LOWER"))
                    
                    for price, volume, label in cliff_stats:
                        fig.add_annotation(
                            x=profile_start - profile_width * 0.45,  # Position further left
                            y=price,
                            text=f"{label}: €{price:.0f} | V: {volume:,.0f}",
                            showarrow=False,
                            font=dict(color="rgba(0, 191, 255, 0.95)", size=8, family="Arial"),  # Deep sky blue
                            bgcolor="rgba(0, 0, 0, 0.85)",
                            bordercolor="rgba(0, 191, 255, 0.8)",
                            borderwidth=1,
                            xanchor="right",
                            row=1, col=1
                        )
                
                if show_quartile_labels:
                    # Calculate quartiles based on volume-weighted prices
                    min_price = sig_prices.min()
                    max_price = sig_prices.max()
                    
                    # Volume-weighted percentiles
                    sorted_indices = np.argsort(sig_prices)
                    sorted_prices = sig_prices[sorted_indices]
                    sorted_volumes = sig_volumes[sorted_indices]
                    
                    cumulative_volume = np.cumsum(sorted_volumes)
                    total_volume = cumulative_volume[-1]
                    
                    # Find quartile prices
                    q1_idx = np.searchsorted(cumulative_volume, total_volume * 0.25)
                    q3_idx = np.searchsorted(cumulative_volume, total_volume * 0.75)
                    
                    q1_price = sorted_prices[min(q1_idx, len(sorted_prices)-1)]
                    q3_price = sorted_prices[min(q3_idx, len(sorted_prices)-1)]
                    
                    # Get volumes at these levels
                    min_vol = sig_volumes[np.argmin(sig_prices)]
                    max_vol = sig_volumes[np.argmax(sig_prices)]
                    q1_vol = sorted_volumes[min(q1_idx, len(sorted_volumes)-1)]
                    q3_vol = sorted_volumes[min(q3_idx, len(sorted_volumes)-1)]
                    
                    # Add quartile labels
                    quartile_stats = [
                        (min_price, min_vol, "MIN"),
                        (q1_price, q1_vol, "Q1"),
                        (q3_price, q3_vol, "Q3"),
                        (max_price, max_vol, "MAX")
                    ]
                    
                    for price, volume, label in quartile_stats:
                        fig.add_annotation(
                            x=profile_start - profile_width * 0.3,
                            y=price,
                            text=f"{label}: €{price:.0f} | V: {volume:,.0f}",
                            showarrow=False,
                            font=dict(color="rgba(255, 255, 255, 0.95)", size=8, family="Arial"),
                            bgcolor="rgba(0, 0, 0, 0.85)",
                            bordercolor="rgba(255, 255, 255, 0.8)",
                            borderwidth=1,
                            xanchor="right",
                            row=1, col=1
                        )
                
                if show_poc_labels:
                    # Add POC label
                    fig.add_annotation(
                        x=profile_start - profile_width * 0.3,
                        y=profile_data['poc'],
                        text=f"POC: €{profile_data['poc']:.0f} | V: {poc_volume:,.0f}",
                        showarrow=False,
                        font=dict(color="rgba(255, 215, 0, 0.95)", size=8, family="Arial"),
                        bgcolor="rgba(0, 0, 0, 0.85)",
                        bordercolor="rgba(255, 215, 0, 0.95)",
                        borderwidth=1,
                        xanchor="right",
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
    st.title("📈 AI Session Profile Monitor")
    st.markdown("Real-time DAX analysis with Session Volume Profile and AI insights")
    
    # Instructions
    with st.expander("📋 Quick Instructions", expanded=False):
        st.markdown("""
        **Getting Started:**
        - ⚠️ **Try the AI at the bottom of the page!** Now with custom prompt support! ⚠️
        - **Viewing Timeframe**: Select 5d for desktop, 1 day for mobile devices
        - **Chart Navigation**: If chart moves accidentally, refresh the page to reset view
        - **Labels**: Try enabling volume cliff or quartile labels
        - **AI Analysis**: Selected annotation labels (POC, Quartiles, Volume Cliffs) are automatically included in AI analysis
        - **Session Profiles**: Blue bars show volume distribution, yellow POC line shows highest volume price level
        """)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        period = st.selectbox(
            "Timeframe",
            ["1d", "5d", "1mo"],
            index=0
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
    
    with col4:
        show_poc_labels = st.checkbox("POC Labels", value=True)
        show_quartile_labels = st.checkbox("Quartile Labels", value=False)
        show_cliff_labels = st.checkbox("Volume Cliffs", value=False)
    
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
    
    fig = create_candlestick_chart(df, daily_profiles, show_poc_labels, show_quartile_labels, show_cliff_labels)
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
                        
                        # Collect annotation data for LLM analysis
                        annotation_data = {}
                        if show_quartile_labels or show_cliff_labels:
                            # Calculate the same annotation data that's displayed
                            prices = np.array(latest_profile['price_levels'])
                            volumes = np.array(latest_profile['volume_profile'])
                            max_volume = max(volumes) if max(volumes) > 0 else 1
                            significant_mask = volumes > max_volume * 0.05
                            sig_prices = prices[significant_mask]
                            sig_volumes = volumes[significant_mask]
                            
                            if len(sig_prices) > 0:
                                if show_quartile_labels:
                                    # Calculate quartiles
                                    sorted_indices = np.argsort(sig_prices)
                                    sorted_prices = sig_prices[sorted_indices]
                                    sorted_volumes = sig_volumes[sorted_indices]
                                    cumulative_volume = np.cumsum(sorted_volumes)
                                    total_volume = cumulative_volume[-1]
                                    
                                    q1_idx = np.searchsorted(cumulative_volume, total_volume * 0.25)
                                    q3_idx = np.searchsorted(cumulative_volume, total_volume * 0.75)
                                    
                                    annotation_data['quartiles'] = {
                                        'min': {'price': sig_prices.min(), 'volume': sig_volumes[np.argmin(sig_prices)]},
                                        'q1': {'price': sorted_prices[min(q1_idx, len(sorted_prices)-1)], 'volume': sorted_volumes[min(q1_idx, len(sorted_volumes)-1)]},
                                        'q3': {'price': sorted_prices[min(q3_idx, len(sorted_prices)-1)], 'volume': sorted_volumes[min(q3_idx, len(sorted_volumes)-1)]},
                                        'max': {'price': sig_prices.max(), 'volume': sig_volumes[np.argmax(sig_prices)]}
                                    }
                                
                                if show_cliff_labels:
                                    # Calculate cliffs
                                    poc_idx = np.argmax(volumes)
                                    poc_volume_threshold = max_volume * 0.6
                                    cliffs = {}
                                    
                                    # Upper cliff
                                    for i in range(poc_idx, len(volumes)):
                                        if volumes[i] < poc_volume_threshold and volumes[i] > max_volume * 0.1:
                                            cliffs['upper'] = {'price': prices[i], 'volume': volumes[i]}
                                            break
                                    
                                    # Lower cliff
                                    for i in range(poc_idx, -1, -1):
                                        if volumes[i] < poc_volume_threshold and volumes[i] > max_volume * 0.1:
                                            cliffs['lower'] = {'price': prices[i], 'volume': volumes[i]}
                                            break
                                    
                                    annotation_data['cliffs'] = cliffs
                        
                        analyzer = LLMAnalyzer()
                        analysis = analyzer.analyze_price_action(df, latest_profile, custom_prompt, annotation_data)
                        st.markdown(analysis)
                    else:
                        st.error("No volume profile data available for analysis")
                except Exception as e:
                    st.error(f"AI analysis failed: {str(e)}")
                    st.info("Make sure to set your ANTHROPIC_API_KEY in .streamlit/secrets.toml")
    
    # Footer
    st.markdown("---")
    st.markdown("*AI Session Profile Monitor - Built with Streamlit, Polars, and Claude AI*")

if __name__ == "__main__":
    main()