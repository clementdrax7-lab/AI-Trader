import time
import pandas as pd
import MetaTrader5 as mt5

class MT5DataFeed:
    def __init__(self, symbol: str, timeframe: int):
        self.symbol = symbol
        self.timeframe = timeframe  # e.g., mt5.TIMEFRAME_M15

    def connect(self) -> bool:
        """Initializes connection to the active desktop MT5 terminal."""
        if not mt5.initialize():
            print(f"MT5 Initialization failed. Error code: {mt5.last_error()}")
            return False
        
        # Verify if asset is visible in Market Watch
        if not mt5.symbol_select(self.symbol, True):
            print(f"Symbol {self.symbol} not found.")
            mt5.shutdown()
            return False
        return True

    def get_latest_candles(self, count: int = 100) -> pd.DataFrame:
        """Fetches the most recent completed and active candlestick bars."""
        rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, count)
        if rates is None or len(rates) == 0:
            raise RuntimeError(f"Failed to fetch data for {self.symbol}")
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        # Structure columns uniformly for your analyzers
        df = df.rename(columns={'tick_volume': 'volume'})
        return df[['time', 'open', 'high', 'low', 'close', 'volume']]

    def disconnect(self):
        """Safely disconnects from the MT5 terminal API wrapper."""
        mt5.shutdown()
