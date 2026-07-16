class TradeSetup:

    def __init__(self, symbol, direction, entry, stop_loss, take_profit, confidence):

        self.symbol = symbol
        self.direction = direction
        self.entry = entry
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.confidence = confidence


    def display(self):

        print("\n------ TRADE SETUP ------")
        print("Symbol:", self.symbol)
        print("Direction:", self.direction)
        print("Entry:", self.entry)
        print("Stop Loss:", self.stop_loss)
        print("Take Profit:", self.take_profit)
        print("Confidence:", self.confidence, "%")