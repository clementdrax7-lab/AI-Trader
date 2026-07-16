from ict import ICTAnalyzer
from support_resistance import SupportResistanceAnalyzer
from risk import RiskManager
from trade_setup import TradeSetup


class TradingAI:

    def __init__(self, market):
        self.market = market
        self.ict = ICTAnalyzer()
        self.sr = SupportResistanceAnalyzer()
        self.risk = RiskManager()


    def analyze(self):

        print("\nAnalyzing:", self.market)


        candles = [
            {
                "open": 2350,
                "high": 2360,
                "low": 2345,
                "close": 2355
            },
            {
                "open": 2355,
                "high": 2370,
                "low": 2352,
                "close": 2368
            }
        ]


        ict_result = self.ict.analyze(candles)
        sr_result = self.sr.analyze(candles)


        risk_result = self.risk.calculate(
            balance=1000,
            risk_percent=1,
            stop_loss_points=50,
            reward_ratio=2
        )


        print("\nICT:")
        print(ict_result)

        print("\nSupport/Resistance:")
        print(sr_result)

        print("\nRisk:")
        print(risk_result)


        confidence = (
            ict_result["score"] +
            sr_result["score"]
        )


        print("\nAI Confidence:", confidence)


        if confidence >= 40 and risk_result["risk_allowed"]:

            trade = TradeSetup(
                symbol=self.market,
                direction="BUY",
                entry=2365.0,
                stop_loss=2355.0,
                take_profit=2385.0,
                confidence=confidence
            )

            trade.display()

            return "BUY"


        return "NO TRADE"



ai = TradingAI("XAUUSD")

signal = ai.analyze()

print("\nSIGNAL:", signal)