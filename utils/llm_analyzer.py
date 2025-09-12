import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

class LLMAnalyzer:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    def analyze_price_action(self, df, volume_profile_data, custom_prompt=None):
        summary = self._create_price_summary(df, volume_profile_data)
        
        if custom_prompt:
            prompt = custom_prompt.format(summary=summary)
        else:
            prompt = f"""
Analyze this DAX price action data and provide a concise trading report:

{summary}

Please provide:
1. Market Sentiment (Bullish/Bearish/Neutral)
2. Key Support/Resistance Levels
3. Volume Analysis Insights
4. Potential Trading Opportunities
5. Risk Considerations

Keep the analysis practical and actionable for traders.
"""
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            return f"Analysis unavailable: {str(e)}"
    
    def _create_price_summary(self, df, volume_profile_data):
        latest = df.tail(1).to_dicts()[0]
        recent_data = df.tail(20)
        
        first_close = df.head(1)['close'][0]
        price_change = latest['close'] - first_close
        price_change_pct = (price_change / first_close * 100) if first_close != 0 else 0
        
        high_52w = df['high'].max()
        low_52w = df['low'].min()
        avg_volume = df['volume'].mean()
        recent_volume = recent_data['volume'].mean()
        
        volume_trend = "Higher" if avg_volume > 0 and recent_volume > avg_volume else "Lower"
        
        volume_ratio = f"{(recent_volume/avg_volume):.2f}x" if avg_volume > 0 else "N/A"
        volatility = f"{((recent_data['high'].max() - recent_data['low'].min()) / recent_data['close'].mean() * 100):.1f}%" if recent_data['close'].mean() > 0 else "N/A"
        
        summary = f"""
PRICE DATA:
- Current Price: {latest['close']:.2f}
- Price Change: {price_change:+.2f} ({price_change_pct:+.2f}%)
- 52W High: {high_52w:.2f}
- 52W Low: {low_52w:.2f}
- Recent High: {recent_data['high'].max():.2f}
- Recent Low: {recent_data['low'].min():.2f}

VOLUME ANALYSIS:
- Point of Control (POC): {volume_profile_data['poc']:.2f}
- Total Session Volume: {volume_profile_data['total_volume']:,.0f}
- Average Volume: {avg_volume:,.0f}
- Recent Volume Trend: {volume_trend} than average
- Volume Ratio: {volume_ratio}

TECHNICAL CONTEXT:
- Trading Range: {recent_data['low'].min():.2f} - {recent_data['high'].max():.2f}
- Volatility: {volatility}
"""
        return summary