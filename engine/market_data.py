class MarketData:

    def get_candles(self, symbol, timeframe, amount):

        print("Loading market data...")
        print("Symbol:", symbol)
        print("Timeframe:", timeframe)

        # Temporary candle data
        candles = [
            {
                "open": 2350,
                "high": 2360,
                "low": 2345,
                "close": 2358
            },
            {
                "open": 2358,
                "high": 2370,
                "low": 2355,
                "close": 2365
            }
        ]

        return candles
