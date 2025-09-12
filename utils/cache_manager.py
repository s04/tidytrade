import os
import polars as pl
from datetime import datetime, timedelta
from pathlib import Path

class CacheManager:
    def __init__(self, cache_dir="cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_cache_path(self, symbol, period, interval):
        filename = f"{symbol}_{period}_{interval}.parquet"
        return self.cache_dir / filename
    
    def is_cache_valid(self, cache_path, max_age_hours=1):
        if not cache_path.exists():
            return False
        
        file_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        return file_age < timedelta(hours=max_age_hours)
    
    def save_data(self, df, symbol, period, interval):
        cache_path = self.get_cache_path(symbol, period, interval)
        df.write_parquet(cache_path)
    
    def load_data(self, symbol, period, interval):
        cache_path = self.get_cache_path(symbol, period, interval)
        if self.is_cache_valid(cache_path):
            return pl.read_parquet(cache_path)
        return None