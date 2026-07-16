import pandas as pd

class BreakRetestAnalyzer:
    """Validates classic S&R validation flips alongside structural breakout retests."""
    def __init__(self, touch_margin_pct: float = 0.0005):
        self.margin = touch_margin_pct

    def evaluate_retest(self, df: pd.DataFrame, bias: int) -> dict:
        """Looks for price retracing back into a broken level."""
        if len(df) < 5 or bias == 0:
            return {"setup": False, "level": None}

        last_close = df['close'].iloc[-1]
        last_low = df['low'].iloc[-1]
        last_high = df['high'].iloc[-1]

        # Bullish: Support flipped to Resistance Retest (Looking for shorts)
        if bias == -1 and not pd.isna(df['Active_Low'].iloc[-1]):
            broken_level = df['Active_Low'].iloc[-1]
            # Price breaks below, now retracing up to touch former support from below
            if last_high >= broken_level * (1 - self.margin) and last_close <= broken_level:
                return {"setup": True, "type": "Bearish_Retest", "level": broken_level}

        # Bearish: Resistance flipped to Support Retest (Looking for longs)
        elif bias == 1 and not pd.isna(df['Active_High'].iloc[-1]):
            broken_level = df['Active_High'].iloc[-1]
            # Price breaks above, now dipping down to test former resistance as support
            if last_low <= broken_level * (1 + self.margin) and last_close >= broken_level:
                return {"setup": True, "type": "Bullish_Retest", "level": broken_level}

        return {"setup": False, "level": None}
