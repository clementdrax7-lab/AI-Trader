class ICTAnalyzer:

    def analyze(self, candles):

        score = 0
        reasons = []

        if len(candles) < 3:
            return {
                "score": 0,
                "reasons": ["Not enough candle data"]
            }


        # Get recent candles
        previous = candles[-2]
        current = candles[-1]


        # Break of Structure (simple bullish BOS)
        if current["high"] > previous["high"]:
            score += 30
            reasons.append("Bullish break of structure")


        # Liquidity sweep detection
        if current["low"] < previous["low"] and current["close"] > previous["low"]:
            score += 25
            reasons.append("Liquidity sweep detected")


        # Bullish candle confirmation
        if current["close"] > current["open"]:
            score += 20
            reasons.append("Bullish candle confirmation")


        return {
            "score": score,
            "reasons": reasons
        }
