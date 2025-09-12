import yfinance as yf
import polars as pl
from .cache_manager import CacheManager

class DataFetcher:
    def __init__(self):
        self.cache = CacheManager()
    
    def fetch_dax_data(self, period="1y", interval="1d"):
        cached_data = self.cache.load_data("DAX", period, interval)
        if cached_data is not None:
            return cached_data
        
        ticker = yf.Ticker("^GDAXI")
        df_pandas = ticker.history(period=period, interval=interval)
        
        df_polars = pl.from_pandas(df_pandas.reset_index())
        
        df_polars = df_polars.with_columns([
            pl.col("Datetime").alias("datetime"),
            pl.col("Open").alias("open"),
            pl.col("High").alias("high"), 
            pl.col("Low").alias("low"),
            pl.col("Close").alias("close"),
            pl.col("Volume").alias("volume")
        ]).select(["datetime", "open", "high", "low", "close", "volume"])
        
        # Handle zero volume by creating synthetic volume based on price volatility
        df_polars = df_polars.with_columns([
            pl.when(pl.col("volume") == 0)
            .then(
                (((pl.col("high") - pl.col("low")) / pl.col("close")) * 10000000 + 
                 (pl.col("close") - pl.col("open")).abs() * 50000).cast(pl.Int64)
            )
            .otherwise(pl.col("volume"))
            .alias("volume")
        ])
        
        self.cache.save_data(df_polars, "DAX", period, interval)
        return df_polars