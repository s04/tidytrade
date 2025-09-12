import numpy as np
import polars as pl
from datetime import time

class SessionVolumeProfile:
    def __init__(self, price_bins=50):
        self.price_bins = price_bins
    
    def calculate(self, df, session_start=None, session_end=None):
        if session_start and session_end:
            df = self._filter_session(df, session_start, session_end)
        
        price_min = df['low'].min()
        price_max = df['high'].max()
        
        price_levels = np.linspace(price_min, price_max, self.price_bins + 1)
        volume_profile = np.zeros(self.price_bins)
        
        for row in df.iter_rows(named=True):
            low, high, volume = row['low'], row['high'], row['volume']
            
            start_bin = np.searchsorted(price_levels, low, side='right') - 1
            end_bin = np.searchsorted(price_levels, high, side='left')
            
            start_bin = max(0, start_bin)
            end_bin = min(self.price_bins - 1, end_bin)
            
            bins_touched = end_bin - start_bin + 1
            volume_per_bin = volume / bins_touched if bins_touched > 0 else 0
            
            for i in range(start_bin, end_bin + 1):
                if i < self.price_bins:
                    volume_profile[i] += volume_per_bin
        
        price_centers = (price_levels[:-1] + price_levels[1:]) / 2
        
        return {
            'price_levels': price_centers,
            'volume_profile': volume_profile,
            'poc': price_centers[np.argmax(volume_profile)],
            'total_volume': df['volume'].sum()
        }
    
    def calculate_daily_profiles(self, df):
        df = df.with_columns(pl.col('datetime').dt.date().alias('date'))
        daily_profiles = {}
        
        for date in df['date'].unique().sort():
            daily_data = df.filter(pl.col('date') == date)
            if len(daily_data) > 0:
                profile = self.calculate(daily_data)
                daily_profiles[str(date)] = profile
                
        return daily_profiles
    
    def _filter_session(self, df, session_start, session_end):
        df = df.with_columns(
            pl.col('datetime').dt.time().alias('time')
        )
        
        return df.filter(
            (pl.col('time') >= session_start) & 
            (pl.col('time') <= session_end)
        )