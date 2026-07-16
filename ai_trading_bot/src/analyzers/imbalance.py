import pandas as pd

class FVGDetector:
    """Identifies Fair Value Gaps (FVG) and structural market imbalances."""
    def __init__(self, min_gap_pips: float = 0.00005):
        self.min_gap = min_gap_pips

    def scan_for_fvgs(self, df: pd.DataFrame) -> dict:
        """Checks if the most recent completed market structures contain an unmitigated FVG."""
        if len(df) < 4:
            return {"bullish_fvg": False, "bearish_fvg": False, "level": None}

        # Check standard 3-candle patterns (Candles i-2, i-1, i)
        high_minus_2 = df['high'].iloc[-3]
        low_minus_2 = df['low'].iloc[-3]
        
        high_current = df['high'].iloc[-1]
        low_current = df['low'].iloc[-1]
        
        last_close = df['close'].iloc[-1]

        # Bullish FVG: Low of candle 3 is higher than High of candle 1
        if low_current > high_minus_2 + self.min_gap:
            # Mitigation check: Current price has not dropped back down to close the gap yet
            if last_close > low_current:
                return {"bullish_fvg": True, "bearish_fvg": False, "level": (low_current + high_minus_2) / 2}

        # Bearish FVG: High of candle 3 is lower than Low of candle 1
        if high_current < low_minus_2 - self.min_gap:
            # Mitigation check: Current price has not rallied back up to close the gap yet
            if last_close < high_current:
                return {"bullish_fvg": False, "bearish_fvg": True, "level": (high_current + low_minus_2) / 2}

        return {"bullish_fvg": False, "bearish_fvg": False, "level": None}
