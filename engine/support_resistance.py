class SupportResistanceAnalyzer:

    def analyze(self, candles):

        score = 0
        reasons = []


        if len(candles) < 3:
            return {
                "score": 0,
                "reasons": ["Not enough candle data"]
            }


        previous = candles[-2]
        current = candles[-1]


        # Resistance break
        if current["high"] > previous["high"]:
            score += 25
            reasons.append("Resistance break detected")


        # Support hold
        if current["low"] >= previous["low"]:
            score += 25
            reasons.append("Support holding")


        # Retest confirmation
        if current["close"] > current["open"]:
            score += 20
            reasons.append("Bullish retest confirmation")


        return {
            "score": score,
            "reasons": reasons
        }
