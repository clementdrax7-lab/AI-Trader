import pandas as pd
import numpy as np

class ChartPrimeSMC:
    """Calculates Market Structure Breaks and Order Block coordinates."""
    def __init__(self, swing_length: int = 10):
        self.length = swing_length

    def analyze_structure(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['BOS'] = False
        df['CHoCH'] = False
        df['Structure_Bias'] = 0 # 1 = Bullish, -1 = Bearish
        
        # Discover localized technical swing high/low coordinates
        for i in range(self.length, len(df) - self.length):
            window = df.iloc[i - self.length : i + self.length + 1]
            
            if df['high'].iloc[i] == window['high'].max():
                df.loc[df.index[i], 'Swing_High'] = df['high'].iloc[i]
            if df['low'].iloc[i] == window['low'].min():
                df.loc[df.index[i], 'Swing_Low'] = df['low'].iloc[i]
                
        # Forward fill key level metrics to evaluate active breakouts
        df['Active_High'] = df['Swing_High'].ffill()
        df['Active_Low'] = df['Swing_Low'].ffill()

        current_bias = 0
        for i in range(1, len(df)):
            # Bullish Breakout Logic: Candle closes cleanly over previous structural boundaries
            if df['close'].iloc[i] > df['Active_High'].iloc[i-1] and df['close'].iloc[i-1] <= df['Active_High'].iloc[i-1]:
                if current_bias == -1:
                    df.loc[df.index[i], 'CHoCH'] = True  # Shift in directional bias
                else:
                    df.loc[df.index[i], 'BOS'] = True    # Trend extension breakout
                current_bias = 1
                
            # Bearish Breakout Logic
            elif df['close'].iloc[i] < df['Active_Low'].iloc[i-1] and df['close'].iloc[i-1] >= df['Active_Low'].iloc[i-1]:
                if current_bias == 1:
                    df.loc[df.index[i], 'CHoCH'] = True
                else:
                    df.loc[df.index[i], 'BOS'] = True
                current_bias = -1
                
            df.loc[df.index[i], 'Structure_Bias'] = current_bias
            
        return df
